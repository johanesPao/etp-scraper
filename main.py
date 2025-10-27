from rahasia import Rahasia
from endpoint.rekues import Request
from endpoint.enums import ActionId
from proses import ambil_data
from pemrosesan_data.produk import master_produk_gap_gpa

if __name__ == "__main__":
    rahasia = Rahasia()
    rekues = Request(rahasia.param.url, rahasia.param.id_perusahaan)
    gap = ambil_data(rekues, ActionId.GET_ALL_PRODUCTS, 200)
    gpa = ambil_data(rekues, ActionId.GET_PRODUCT_ALIAS, 200)

    master_produk_gap_gpa(gap, gpa)
