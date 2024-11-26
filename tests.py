from app import db, User

def test_roles():
    users = User.query.all()
    for user in users:
        print(f"User ID: {user.id}, Role: {user.role}")

if __name__ == "__main__":
    test_roles()