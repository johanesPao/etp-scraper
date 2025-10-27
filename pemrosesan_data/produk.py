import polars as pl
import json


def master_produk_gap_gpa(gap: pl.DataFrame, gpa: pl.DataFrame) -> None:
    """
    Fungsi ini menggabungkan data GET_ALL_PRODUCTS (gap) dan
    GET_PRODUCT_ALIAS (gpa) berdasarkan variantIds (gap) dan
    productID (gpa). Hasil penggabungan disimpan dalam file
    JSON.
    """
    df_ekspan_variant_ids = gap.explode("variantIds")
    df_gabungan = df_ekspan_variant_ids.join(
        gpa, left_on="variantIds", right_on="productID", how="full"
    )

    # Print df_gabungan untuk verifikasi
    print(df_gabungan.head(10))
    with open("output/master_produk_gap_gpa.json", "w", encoding="utf-8") as f:
        json.dump(df_gabungan.to_dicts(), f, ensure_ascii=False, indent=4)
