from flask import Flask, render_template, redirect, request, url_for, session, flash
from mysql import connector
from functools import wraps
from datetime import date
import base64
import re


app = Flask(__name__)
app.secret_key = "apotiku"    

db = cursor = None


def openDb():
    global db, cursor
    db = connector.connect(
            host = "localhost",
            user = "root",
            passwd = "",
            database = "db_apotek" 
    )
    if db.is_connected():
        print("Berhasil terhubung dengan database")

    cursor = db.cursor()	

def closeDb():
    global db, cursor
    cursor.close()
    db.close()


@app.route('/login', methods=['GET', 'POST'])
def login(): 
    openDb()    
    msg = ''
    if request.method == 'POST' and 'no_hp' in request.form and 'pass' in request.form:        
        no_hp = request.form['no_hp']
        password = request.form['pass']
        
        cursor.execute('SELECT * FROM member WHERE no_hp= %s AND password = %s', (no_hp, password))        
        account = cursor.fetchone()
        
        if account:
            session['loggedin'] = True
            session['no_hp'] = account[0]
            session['name'] = account[1]
            msg = 'Logged in successfully !'
            return redirect(url_for('index'))

        else:            
            msg = 'No. Handphone / password tidak sesuai!'
    
    closeDb()         
    return render_template('login.html', msg=msg)


def logindulu(f):
	@wraps(f)
	def wrap(*args,**kwargs):
		if 'loggedin' in session:
			return f(*args,**kwargs)
		else:
			flash('Unauthorized, Please Login','danger')
			return render_template('login.html', )
	return wrap


@app.route("/logout")
def logout():
	session.clear() 		
	return redirect(url_for('index'))


@app.route('/')
def index():
    openDb()
    sql = 'select * from obat where stok > 0'
    cursor.execute(sql)
    result = cursor.fetchall() 
    
    cursor.execute('SELECT DISTINCT kategori FROM obat')
    kategori = cursor.fetchall()

    if 'loggedin' in session:
        cursor.execute("SELECT COUNT(*) FROM cart where pelanggan='{}'" .format(session['no_hp']))
        length = cursor.fetchall()     
    else:
        length = 0
    
    closeDb()
    return render_template('index.html', posted1 = result, posted2 = result, kategori = kategori, length = length)


@app.route('/store')
def store():
    openDb()
    sql = ("select * from obat where stok > 0")
    cursor.execute(sql)
    result = cursor.fetchall()  

    kategori = 'SELECT DISTINCT kategori FROM obat'
    cursor.execute(kategori)
    kategori = cursor.fetchall()

    if 'loggedin' in session:
        cursor.execute("SELECT COUNT(*) FROM cart where pelanggan='{}'" .format(session['no_hp']))
        length = cursor.fetchall()     
    else:
        length = 0

    closeDb()
    return render_template('store.html', posted1 = result, length = length, kategori = kategori)
    

@app.route('/store <kate>')
def kategori(kate):
    openDb()
    cursor.execute('select * from obat where kategori=%s and stok > 0', (kate,))
    kategoris = cursor.fetchall()  

    cursor.execute('SELECT DISTINCT kategori FROM obat')
    kategori = cursor.fetchall()

    if 'loggedin' in session:
        cursor.execute("SELECT COUNT(*) FROM cart where pelanggan='{}'" .format(session['no_hp']))
        length = cursor.fetchall() 
    else:
        length = 0

    closeDb()
    return render_template('store.html', kategoris = kategoris, length = length, kategori = kategori)


@app.route('/result', methods = ['POST', 'GET'])
def result():
    openDb()
    kata_kunci = request.args.get('q')
    cursor.execute("select * from obat where nama_obat like '%{}%'" .format(kata_kunci))
    result1 = cursor.fetchall()

    cursor.execute('SELECT DISTINCT kategori FROM obat')
    kategori = cursor.fetchall()

    if 'loggedin' in session:
        cursor.execute("SELECT COUNT(*) FROM cart where pelanggan='{}'" .format(session['no_hp']))
        length = cursor.fetchall() 
    else:
        length = 0

    closeDb()
    return render_template('pencarian.html', keyword = result1, length = length, kategori = kategori)


@app.route('/produk <nama_produk>')
def store_view(nama_produk):
    openDb()    
    cursor.execute("select * from obat where nama_obat='{}'" .format(nama_produk))
    result = cursor.fetchall()

    cursor.execute('SELECT DISTINCT kategori FROM obat')
    kategori = cursor.fetchall()

    if 'loggedin' in session:
        cursor.execute("SELECT COUNT(*) FROM cart where pelanggan='{}'" .format(session['no_hp']))
        length = cursor.fetchall() 
    else:
        length = 0

    closeDb()
    return render_template('store-view.html', produk = result, length = length, kategori = kategori)
    

result1 = ''
result2 = 0
@app.route('/addcart', methods=['POST'])
@logindulu
def addcart():    
    try:
        openDb()
        user = request.form['user']
        id_produk = request.form['id_produk']
        qty = int(request.form['qty'])

        result = cursor.execute("SELECT * FROM cart WHERE pelanggan='{}'" .format(user))
        result = cursor.fetchall()
        list(zip(result))
        
        for i in result:   
            global result1, result2
            result1 = i[1]
            result2 = i[2]
        
        
        if id_produk not in result1:        
            sql = 'INSERT INTO cart (pelanggan, produk, jumlah_produk) VALUES (%s, %s, %s)'
            val = (user, id_produk, qty)
            cursor.execute(sql, val)
            db.commit()

        jumlah_qty = result2 + qty
        if id_produk in result1:
            up = "UPDATE cart SET jumlah_produk={} WHERE pelanggan='{}' AND produk='{}' " .format(jumlah_qty, user, id_produk)
            cursor.execute(up)
            db.commit()
                    
                

    except Exception as e:
        print(e)
    finally:        
        return redirect(request.referrer)


@app.route('/updateitem <id_produk>', methods = ['POST'])
@logindulu
def updateitem(id_produk):
    openDb()    
    qty = int(request.form['qty'])

    cursor.execute(" UPDATE cart SET jumlah_produk={} WHERE pelanggan='{}' AND produk='{}' " .format(qty, session['no_hp'], id_produk))
    db.commit()
    
    return redirect(request.referrer)

@app.route('/deleteitem <kode_obat>')
@logindulu
def deleteitem(kode_obat):
    openDb()
    cursor.execute("DELETE FROM cart WHERE pelanggan='{}' AND produk='{}' " .format(session['no_hp'], kode_obat))
    db.commit()
    closeDb()
    return redirect(request.referrer)


@app.route('/cart')
@logindulu
def cart():
    openDb()
    cursor.execute("SELECT * FROM `keranjang_pelanggan` WHERE pelanggan='{}'" . format(session['no_hp']))
    result = cursor.fetchall()
    

    cursor.execute('SELECT DISTINCT kategori FROM obat')
    kategori = cursor.fetchall()

    if 'loggedin' in session:
        cursor.execute("SELECT COUNT(*) FROM cart where pelanggan='{}'" .format(session['no_hp']))
        length = cursor.fetchall() 
    else:
        length = 0

    cursor.execute("SELECT SUM(total_harga) AS grand_total FROM `keranjang_pelanggan` WHERE pelanggan='{}'" .format(session['no_hp']))
    grandtotal = cursor.fetchall()

    return render_template('cart.html', length = length, kategori = kategori, produku = result, grandtotal = grandtotal)


@app.route('/checkout')
@logindulu
def checkout():
    openDb()
    cursor.execute('SELECT DISTINCT kategori FROM obat')
    kategori = cursor.fetchall()

    cursor.execute("SELECT * FROM `keranjang_pelanggan` WHERE pelanggan='{}'" . format(session['no_hp']))
    transaksi = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(kode_obat) FROM `keranjang_pelanggan` WHERE pelanggan='{}'" . format(session['no_hp']))
    jml_produk = cursor.fetchall()

    cursor.execute("SELECT SUM(total_harga) AS grand_total FROM `keranjang_pelanggan` WHERE pelanggan='{}'" .format(session['no_hp']))
    grandtotal = cursor.fetchall()

    if 'loggedin' in session:
        cursor.execute("SELECT COUNT(*) FROM cart where pelanggan='{}'" .format(session['no_hp']))
        length = cursor.fetchall() 
    else:
        length = 0
    
    closeDb()
    return render_template('checkout.html', length = length, kategori = kategori, transaksi = transaksi, grandtotal = grandtotal, jml_produk = jml_produk)


@app.route('/addorder', methods = ['POST'])
def addorder():
    openDb()    
    cursor.execute("SELECT SUM(total_harga) AS grand_total FROM `keranjang_pelanggan` WHERE pelanggan='{}'" .format(session['no_hp']))
    grandtotal = cursor.fetchall()
    grandtotal = grandtotal[0][0]
        
    user = session['no_hp']        
    jml_produk = request.form['jumlah_produk']
    tgl_trans = date.today()        
    cat = request.form['catatan']

    sql = "INSERT INTO transaksi (pelanggan, jumlah_produk, tanggal_transaksi, grand_total, catatan) VALUES (%s, %s, %s, %s, %s) "
    val = (user, jml_produk, tgl_trans, grandtotal, cat)
    cursor.execute(sql, val)
    db.commit()

    cursor.execute('DELETE FROM cart WHERE pelanggan=%s',(session['no_hp'],))
    db.commit()
    

    return redirect(url_for('thankyou'))


@app.route('/done')
@logindulu
def thankyou():
    openDb()
    cursor.execute('SELECT DISTINCT kategori FROM obat')
    kategori = cursor.fetchall()

    if 'loggedin' in session:
        cursor.execute("SELECT COUNT(*) FROM cart where pelanggan='{}'" .format(session['no_hp']))
        length = cursor.fetchall() 
    else:
        length = 0

    closeDb()
    return render_template('thankyou.html', length = length, kategori = kategori)


@app.route('/signup', methods=['GET', 'POST'])
def registrasi():
    openDb()
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'pass' in request.form and 'no_hp' in request.form and 'alamat' in request.form and 'jk' in request.form :
        username = request.form['username']
        password = request.form['pass']
        no_hp = request.form['no_hp']
        alamat = request.form['alamat']
        jk = request.form['jk']
        cursor.execute('SELECT * FROM member WHERE no_hp=%s', (no_hp,))
        account = cursor.fetchone()

        if account:
            msg = 'No. Handphone sudah terdaftar !'        
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username hanya menerima angka dan huruf !'
        elif not username or not password or not no_hp:
            msg = 'Please fill out the form !'
        else:
            cursor.execute('INSERT INTO member (no_hp, nama, password, alamat, jk) values (%s, %s, %s, %s, %s)', (no_hp, username, password, alamat, jk))
            db.commit()            
            msg = 'You have successfully registered !'
            return redirect(url_for('login'))

    elif request.method == 'POST':
        msg = 'Please fill out the form !' 
    closeDb()   
    return render_template('registrasi.html', msg = msg)



@app.route('/profile')
def profile():    
    openDb()
    cursor.execute('SELECT DISTINCT kategori FROM obat')
    kategori = cursor.fetchall()
    if 'loggedin' in session:
        cursor.execute("SELECT COUNT(*) FROM cart where pelanggan='{}'" .format(session['no_hp']))
        length = cursor.fetchall() 
    else:
        length = 0

    if 'loggedin' in session:        
        cursor.execute('SELECT * FROM member WHERE no_hp = {}' .format(session['no_hp']))
        account = cursor.fetchone()
        return render_template('profile.html', account = account, length = length, kategori = kategori)
    
    closeDb()
    return redirect(url_for('login'))





# --------------------------- Administrasi-----------------------#

@app.route('/login/admin', methods=['GET', 'POST'])
def login_admin(): 
    openDb()    
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'pass' in request.form:        
        username = request.form['username']
        password = request.form['pass']
        
        cursor.execute('SELECT * FROM login WHERE username= %s AND password = %s', (username, password))        
        account = cursor.fetchone()
        
        if account:
            session['loggedin'] = True
            session['id_login'] = account[1]
            session['username'] = account[2]
            msg = 'Logged in successfully !'
            return redirect(url_for('dataproduk'))

        else:            
            msg = 'Username / password tidak sesuai!'
    
    closeDb()         
    return render_template('admin/login.html', msg=msg)


def logindulu_admin(f):
	@wraps(f)
	def wrap_admin(*args,**kwargs):
		if 'loggedin' in session:
			return f(*args,**kwargs)
		else:
			flash('Unauthorized, Please Login','danger')
			return render_template('admin/login.html')
	return wrap_admin


@app.route("/logout/admin")
def logout_admin():
	session.clear()
	flash('You are now logged out','success')
	return redirect(url_for('index'))



@app.route('/administrasi/')
@logindulu_admin
def dataproduk():
    openDb()
    sql = 'select * from obat '
    cursor.execute(sql)
    result = cursor.fetchall()  
    closeDb()
    return render_template('admin/dataobat.html', post = result)

def render_picture(data):    
    render_pic = base64.b64encode(data).decode('ascii') 
    return render_pic

@app.route('/admin/uploadfile/', methods = ['POST', 'GET'])
@logindulu_admin
def upload():
    if request.method == 'POST':
        kodeproduk = request.form['kodeproduk']
        namaproduk = request.form['namaproduk']
        harga = request.form['harga']
        kategori = request.form['kategori']
        stok = request.form['stok']
        kegunaan = request.form['kegunaan']
        file_gambar = request.files['gambar'].read()
        gambar = render_picture(file_gambar)

        openDb()
        sql = 'insert into obat (kode_obat, nama_obat, harga, kategori, stok, kegunaan, file_gambar, gambar) values (%s, %s, %s, %s, %s, %s, %s, %s)'
        val = (kodeproduk, namaproduk, harga, kategori, stok, kegunaan, file_gambar, gambar)
        cursor.execute(sql, val)
        db.commit()
        closeDb()
        return redirect(url_for('dataproduk'))
    else:
        return render_template('admin/upload.html')


@app.route('/admin/updatedata/', methods = ['POST', 'GET'])
@logindulu_admin
def update_data():
    if request.method == 'POST' :
        kodeproduk = request.form['kodeproduk']
        namaproduk = request.form['namaproduk']
        harga = request.form['harga']
        kategori = request.form['kategori']
        stok = request.form['stok']
        kegunaan = request.form['kegunaan']
        file_gambar = request.files['gambar'].read()
        gambar = render_picture(file_gambar)

        openDb()
        sql = "UPDATE obat SET kode_obat=%s, nama_obat=%s, harga=%s, kategori=%s, stok=%s, kegunaan=%s, file_gambar=%s, gambar=%s WHERE kode_obat=%s "
        val = (kodeproduk, namaproduk, harga, kategori, stok, kegunaan, file_gambar, gambar, kodeproduk)
        cursor.execute(sql, val)
        db.commit()
        closeDb()
        return redirect(url_for('dataproduk'))


@app.route('/result/admin`', methods = ['POST', 'GET'])
@logindulu_admin
def result_admin():
    openDb()
    kata_kunci = request.args.get('q')
    cursor.execute("select * from obat where nama_obat like '%{}%'" .format(kata_kunci))
    result1 = cursor.fetchall()
    closeDb()
    return render_template('admin/pencarian.html', keyword = result1)


@app.route('/admin/hapusdata/<string:kodeproduk>', methods = ['GET'])
@logindulu_admin
def hapus_data(kodeproduk):
   openDb()
   cursor.execute('DELETE FROM obat WHERE kode_obat=%s',(kodeproduk,))
   db.commit()
   closeDb()
   return redirect(url_for('dataproduk'))

if __name__ == '__main__':
    app.debug = True
    app.run()
    