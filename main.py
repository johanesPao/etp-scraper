from rahasia import Rahasia
from endpoint.rekues import Request
from endpoint.enums import ActionId
from proses import ambil_data

if __name__ == "__main__":
    rahasia = Rahasia()
    rekues = Request(rahasia.param.url, rahasia.param.id_perusahaan)
    proses = ambil_data(rekues, ActionId.GET_ALL_PRODUCTS, limit=200)
    print(proses)
