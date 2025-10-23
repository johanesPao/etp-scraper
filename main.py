from rahasia import Rahasia
from endpoint.rekues import Request
from proses import all_products

if __name__ == "__main__":
    rahasia = Rahasia()
    rekues = Request(rahasia.param.url, rahasia.param.id_perusahaan)
    proses = all_products(rekues, limit=200)
    print(proses)
