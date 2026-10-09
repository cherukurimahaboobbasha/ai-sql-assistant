from database import SessionLocal, init_db, User, Product, Order

def seed():
    init_db()
    db = SessionLocal()

    # Avoid duplicate seeding
    if db.query(User).first():
        print("Database already contains data.")
        db.close()
        return

    # Seed Users
    u1 = User(name="Alice Smith", email="alice@example.com")
    u2 = User(name="Bob Jones", email="bob@example.com")
    
    # Seed Products
    p1 = Product(name="Wireless Mouse", category="Electronics", price=29.99, stock=100)
    p2 = Product(name="Mechanical Keyboard", category="Electronics", price=89.99, stock=50)
    p3 = Product(name="Coffee Mug", category="Home", price=12.50, stock=200)

    db.add_all([u1, u2, p1, p2, p3])
    db.commit()

    # Seed Orders
    o1 = Order(user_id=u1.id, product_id=p1.id, quantity=2, total_amount=59.98)
    o2 = Order(user_id=u2.id, product_id=p2.id, quantity=1, total_amount=89.99)

    db.add_all([o1, o2])
    db.commit()
    db.close()
    print("Database seeded successfully with sample records!")

if __name__ == "__main__":
    seed()