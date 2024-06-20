# Aplikasi Apotik Flask


## Instalasi

1. Masuk ke dalam mysql dengan username dan password.
2. Buat database dengan nama **db_apotek**.
3. Jalankan perintah dibawah menggunakan command prompt untuk import database.

    ```sh
    mysql -u username -p db_apotek < database/db_apotek.sql
    ```

4. Buat virtual environment `python -m venv venv`.
5. Masuk virtual environment `source venv/Script/activate`.
6. Install dependecies `pip install -r requirements.txt`.
7. Jalankan server `python app.py`


## Fitur

Terdapat 2 halaman user:

- Admin: **127.0.0.1:5000/administrasi/**
- Customer: **127.0.0.1:5000**

