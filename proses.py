import polars as pl
import time
from typing import Any
import os
import json
from endpoint.rekues import Request
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


def ambil_data(
    rekues: Request, action: ActionId, limit: int | None = None
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

    while True:
        try:
            batch = rekues.fetch_batch_req(action, offset_halaman)
        except Exception as e:
            print(
                f"[{action.name}] Terjadi kesalahan rekues pada halaman {offset_halaman}: {e}. Mencoba lagi..."
            )
            time.sleep(2)
            continue

        # Mengambil data unik dari batch yang belum terunduh
        data_baru = [d for d in batch if d.get(data_id) not in data_id_terunduh]

        if data_baru:
            # Rest ronde_kosong jika ada data baru
            ronde_kosong = 0
            # Tambahkan hanya data baru ke id_terunduh dan semua_data
            for d in data_baru:
                did = d.get(data_id)
                if did not in data_id_terunduh:
                    data_id_terunduh.add(did)
                    semua_data.append(d)
                print(
                    f"[{action.name}] pageCount={offset_halaman} -> Ditemukan {len(batch)} data, {len(data_baru)} diantaranya adalah data baru, total data terkumpul: {len(semua_data)}"
                )
        else:
            # Tambahkan ronde_kosong jika tidak ada data baru
            ronde_kosong += 1
            print(
                f"[{action.name}] pageCount={offset_halaman} -> Ditemukan {len(batch)} data, tidak ada data baru (ronde_kosong: {ronde_kosong})"
            )

        # Kondisi terminasi
        if not batch:
            # Tidak ada data yang dikembalikan -> kemungkinan selesai
            print(
                f"[{action.name}] Tidak ada data yang dikembalikan. Mengakhiri proses pengunduhan."
            )
            break

        if ronde_kosong >= rekues.MAKS_RONDE_KOSONG:
            print(
                f"[{action.name}] Tidak ada data baru selama {rekues.MAKS_RONDE_KOSONG} ronde berturut-turut. Mengakhiri proses untuk mencegah infinite loop"
            )

        # Persiapan untuk iterasi berikutnya
        offset_halaman += rekues.JUMLAH_PER_HALAMAN
        # Cek batas limit jika diberikan
        if limit and len(semua_data) >= limit:
            print(
                f"[{action.name}] Mencapai batas limit {limit} data. Mengakhiri proses pengunduhan."
            )
            break
        # Throttling untuk menghindari hit rate limit
        time.sleep(0.2)

    output_json(
        pl.DataFrame(semua_data),
        f"{action.name.lower()}{f'_limit_{limit}' if limit else ''}",
    )

    return pl.DataFrame(semua_data)
