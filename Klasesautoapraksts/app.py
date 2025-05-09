import sqlite3
from flask import Flask, render_template, g, abort

app = Flask(__name__)
DATABASE = 'cars_project.db' 
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row 
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    try:
        cur = get_db().execute(query, args)
        rv = cur.fetchall()
    
        cur.close()
        return (rv[0] if rv else None) if one else rv
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None 
@app.route('/')
def index():
    """Sākumlapa: Rāda visu mašīnu sarakstu ar ražotāju."""
    
    sql = """
        SELECT 
            m.id, 
            m.modelis, 
            m.gads_no, 
            m.gads_lidz, 
            m.attels_fails, 
            r.nosaukums AS razotaja_nosaukums
        FROM Masinas m
        JOIN Razotaji r ON m.razotajs_id = r.id
        ORDER BY r.nosaukums, m.modelis;
    """
    cars = query_db(sql)
    if cars is None:
        cars = [] 
    return render_template('index.html', cars=cars, page_title="Veco Vācu Auto Katalogs")

@app.route('/car/<int:car_id>')
def car_detail(car_id):
    print(f">>> Ieejam car_detail() maršrutā, car_id: {car_id}") 
    sql_car = """
        SELECT 
            m.*,  -- Visas kolonnas no Masinas tabulas
            r.nosaukums AS razotaja_nosaukums,
            r.logo_attels AS razotaja_logo
        FROM Masinas m
        JOIN Razotaji r ON m.razotajs_id = r.id
        WHERE m.id = ?;
    """
    print(f">>> Mēģinām izpildīt SQL (car_detail - mašīna): {sql_car[:100]}...") 
    car = query_db(sql_car, [car_id], one=True)
    print(f">>> query_db (car_detail - mašīna) atgrieza: {'Dati ir' if car else 'Datu nav vai kļūda'}") 

    
    if car is None:
        print(f"!!! Mašīna ar id={car_id} nav atrasta. Izsaucam abort(404).") 
    print(f">>> Atrastā mašīna: {dict(car)}") 
    sql_categories = """
        SELECT k.nosaukums
        FROM Kategorijas k
        JOIN MasinuKategorijas mk ON k.id = mk.kategorija_id
        WHERE mk.masina_id = ?;
    """
    print(f">>> Mēģinām izpildīt SQL (car_detail - kategorijas): {sql_categories[:100]}...") # Print 6
    categories = query_db(sql_categories, [car_id])
    print(f">>> query_db (car_detail - kategorijas) atgrieza: {'Dati ir' if categories else 'Datu nav vai kļūda'}") # Print 7

    if categories is None:
        print("!!! Kategorijas ir None no query_db, iestatām uz tukšu sarakstu") # Print 8
        categories = []
    else:
         print(f">>> Kategoriju saraksta garums: {len(categories)}") # Print 9
            
    print(f">>> Padodam 'car' un 'categories' uz car_detail.html") # Print 10
    try:
        # IZLABOTĀ RINDAS LOGIKA:
        page_title_value = car['modelis'] 
        print(f">>> Izmantojam page_title: {page_title_value}") 
        return render_template('car_detail.html', car=car, categories=categories, page_title=page_title_value)
    except Exception as e:
        print(f"!!! Kļūda renderējot car_detail.html: {e}")
        import traceback
        traceback.print_exc() 
        return "Kļūda renderējot šablonu car_detail, skatiet termināli."


@app.route('/manufacturer/<int:manufacturer_id>')
def manufacturer_cars(manufacturer_id):
    """Lapa, kas rāda visas mašīnas no konkrēta ražotāja."""
    
    sql_manufacturer = "SELECT nosaukums FROM Razotaji WHERE id = ?;"
    manufacturer = query_db(sql_manufacturer, [manufacturer_id], one=True)
    if manufacturer is None:
        abort(404)
    sql_cars = """
        SELECT id, modelis, attels_fails, gads_no, gads_lidz
        FROM Masinas
        WHERE razotajs_id = ?
        ORDER BY modelis;
    """
    cars = query_db(sql_cars, [manufacturer_id])
    if cars is None:
        cars = []
    return render_template('manufacturer_cars.html', 
                           cars=cars, 
                           manufacturer_name=manufacturer['nosaukums'], 
                           page_title=f"{manufacturer['nosaukums']} Automašīnas")
@app.route('/manufacturers')
def manufacturers():
    print(">>> Ieejam manufacturers() maršrutā")
    sql = "SELECT id, nosaukums, valsts, logo_attels FROM Razotaji ORDER BY nosaukums;"
    print(f">>> Mēģinām izpildīt SQL (manufacturers): {sql}") 
    all_manufacturers = query_db(sql)
    print(f">>> query_db (manufacturers) atgrieza: {'Dati ir' if all_manufacturers else 'Datu nav vai kļūda'}") 
    if all_manufacturers is None:
        print("!!! all_manufacturers ir None no query_db, iestatām uz tukšu sarakstu")
        all_manufacturers = []
    else:
        if len(all_manufacturers) > 0:
            print(f">>> Pirmais ražotājs no saraksta: {dict(all_manufacturers[0])}")
        else:
            print(">>> Saraksts 'all_manufacturers' ir tukšs (bet nav None)")
    print(f">>> Padodam 'all_manufacturers' (garums: {len(all_manufacturers)}) uz manufacturers.html") 
    try:
        return render_template('manufacturers.html', manufacturers=all_manufacturers, page_title="Ražotāji")
    except Exception as e:
        print(f"!!! Kļūda renderējot manufacturers.html: {e}") 
        return "Kļūda renderējot šablonu manufacturers, skatiet termināli."
    
@app.route('/nedarbi')
def nedarbi():
    return render_template ('nedarbi.html')

    



if __name__ == '__main__':
    app.run(debug=True) 