import polars as pl
import time
from typing import Any
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


def ambil_data(
    rekues: Request, action: ActionId, limit: int | None = None
) -> pl.DataFrame:
    id_terunduh: set[Any] = set()
    semua_produk: list[T_Product | T_ProductAlias] = []
    offset_halaman = 0
    ronde_kosong = 0

    atribut_id = id_pencarian(action)
    if atribut_id is None:
        raise ValueError(f"Atribut ID pencarian tidak ditemukan untuk action {action}")

    while True:
        try:
            batch = rekues.fetch_batch_req(action, offset_halaman)
        except Exception as e:
            print(
                f"Terjadi kesalahan rekues pada halaman {offset_halaman}: {e}. Mencoba lagi..."
            )
            time.sleep(2)
            continue

        # Mengambil produk unik dari batch yang belum terunduh
        produk_baru = [p for p in batch if p.get(atribut_id) not in id_terunduh]

        if produk_baru:
            # Rest ronde_kosong jika ada produk baru
            ronde_kosong = 0
            # Tambahkan hanya produk baru ke id_terunduh dan semua_produk
            for p in produk_baru:
                pid = p.get(atribut_id)
                if pid not in id_terunduh:
                    id_terunduh.add(pid)
                    semua_produk.append(p)
                print(
                    f"pageCount={offset_halaman} -> Ditemukan {len(batch)} produk, {len(produk_baru)} diantaranya adalah produk baru, total produk terkumpul: {len(semua_produk)}"
                )
        else:
            # Tambahkan ronde_kosong jika tidak ada produk baru
            ronde_kosong += 1
            print(
                f"pageCount={offset_halaman} -> Ditemukan {len(batch)} produk, tidak ada produk baru (ronde_kosong: {ronde_kosong})"
            )

        # Kondisi terminasi
        if not batch:
            # Tidak ada data yang dikembalikan -> kemungkinan selesai
            print("Tidak ada data yang dikembalikan. Mengakhiri proses pengunduhan.")
            break

        if ronde_kosong >= rekues.MAKS_RONDE_KOSONG:
            print(
                f"Tidak ada data baru selama {rekues.MAKS_RONDE_KOSONG} ronde berturut-turut. Mengakhiri proses untuk mencegah infinite loop"
            )

        # Persiapan untuk iterasi berikutnya
        offset_halaman += rekues.JUMLAH_PER_HALAMAN
        # Cek batas limit jika diberikan
        if limit and len(semua_produk) >= limit:
            print(
                f"Mencapai batas limit {limit} produk. Mengakhiri proses pengunduhan."
            )
            break
        # Throttling untuk menghindari hit rate limit
        time.sleep(0.2)

    return pl.DataFrame(semua_produk)
