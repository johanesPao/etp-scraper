import asyncio
import aiohttp
import polars as pl
import time
from typing import Any
import os
import json
from endpoint.rekues import RequestAsinkron
from endpoint.dict_type import T_Product, T_ProductAlias
from endpoint.enums import ActionId, Attribute


def id_pencarian(action: ActionId) -> Attribute | None:
    match action:
        case ActionId.GET_ALL_PRODUCTS:
            return Attribute.PRODUCT_ID
        case ActionId.GET_PRODUCT_ALIAS:
            return Attribute.PRODUCT_ID_ALIAS
    return None


def output_json(data: pl.DataFrame, nama_file: str) -> None:
    os.makedirs("output", exist_ok=True)
    output_path = f"output/{nama_file}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data.to_dicts(), f, ensure_ascii=False, indent=4)


async def ambil_data(
    rekues: RequestAsinkron,
    action: ActionId,
    limit: int | None = None,
    konkurensi: int = 20,
) -> pl.DataFrame:
    data_id_terunduh: set[Any] = set()
    semua_data: list[T_Product | T_ProductAlias] = []
    offset_halaman = 0
    ronde_kosong = 0

    data_id = id_pencarian(action)
    if data_id is None:
        raise ValueError(
            f"[{action.name}] Atribut ID pencarian tidak ditemukan untuk action {action}"
        )

    waktu_mulai = time.time()

    async with aiohttp.ClientSession() as sesi:
        while True:
            list_offset = [
                offset_halaman + rekues.JUMLAH_PER_HALAMAN * i
                for i in range(konkurensi)
            ]

            # Menjalankan fetch multiple halaman secara konkuren
            pekerjaan = [rekues.fetch_batch_req(sesi, action, o) for o in list_offset]
            hasil = await asyncio.gather(*pekerjaan)

            hasil_batch = [item for sublist in hasil for item in sublist if sublist]

            if not hasil_batch:
                ronde_kosong += 1
                print(
                    f"[{action.name}] Tidak ada data baru (ronde_kosong: {ronde_kosong}), berhenti jika melebihi batas (running time: {(time.time() - waktu_mulai):.2f} detik)"
                )
                if ronde_kosong >= rekues.MAKS_RONDE_KOSONG:
                    break
                await asyncio.sleep(0.5)
                continue

            ronde_kosong = 0
            data_baru = [
                d for d in hasil_batch if d.get(data_id) not in data_id_terunduh
            ]

            for d in data_baru:
                did = d.get(data_id)
                if did not in data_id_terunduh:
                    data_id_terunduh.add(did)
                    semua_data.append(d)

            print(
                f"[{action.name}] +{len(data_baru)} data baru, total {len(semua_data)} (offset: {offset_halaman}, running time: {(time.time() - waktu_mulai):.2f} detik)"
            )

            offset_halaman += rekues.JUMLAH_PER_HALAMAN * konkurensi

            if limit and len(semua_data) >= limit:
                print(
                    f"[{action.name}] Mencapai limit {limit}, berhenti (running time: {(time.time() - waktu_mulai):.2f} detik)"
                )
                break

            await asyncio.sleep(0.2)

    total_waktu = time.time() - waktu_mulai
    print(
        f"\n[{action.name}] Selesai dalam {total_waktu:.2f} detik, total data {len(semua_data)}"
    )

    output_json(
        pl.DataFrame(semua_data),
        f"{action.name.lower()}{f'_limit_{limit}' if limit else ''}",
    )

    return pl.DataFrame(semua_data)
