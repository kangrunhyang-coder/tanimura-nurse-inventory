import os
from datetime import timedelta

from flask import Flask, redirect, request, session, url_for

from config import Config
from models import Area, Item, Stock, db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.permanent_session_lifetime = timedelta(days=30)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(app.instance_path), exist_ok=True)

    db.init_app(app)

    from routes.auth import auth_bp
    from routes.check import check_bp
    from routes.inventory import inventory_bp
    from routes.main import main_bp
    from routes.staff import staff_bp
    from routes.stock import stock_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(stock_bp)
    app.register_blueprint(check_bp)
    app.register_blueprint(staff_bp)

    # Login check for all pages except login/setup/static
    @app.before_request
    def require_login():
        allowed = {"auth.login", "auth.setup", "auth.logout", "main.health", "static"}
        if not session.get("logged_in") and request.endpoint not in allowed:
            return redirect(url_for("auth.login"))

    # Template filter for area item count
    @app.template_filter("count_items")
    def count_items_filter(area_name):
        return Item.query.filter(Item.area == area_name).count()

    with app.app_context():
        db.create_all()
        # Seed areas if empty
        if Area.query.count() == 0:
            for idx, name in enumerate(["1F処置室", "1F診察室", "2F"]):
                db.session.add(Area(name=name, sort_order=idx))
            db.session.commit()
        if Item.query.count() == 0:
            _seed_data()

    return app


def _seed_data():
    """Insert initial item data."""
    items_data = {
        "ボトックス": ["アラガン", "ボツラックス"],
        "スネコス": ["Performa", "1200"],
        "薬品": [
            "酒精綿G個包装", "酒精綿G大", "ヘキシジン綿", "ヒビテン液",
            "タンパク除去液", "アズノールお渡し用",
        ],
        "針": [
            "翼状針21G", "真空管ホルダー", "ニプロVAシリンジ1ml27G付",
            "注射針18G", "注射針22G", "注射針25G", "注射針27G",
            "注射針30G", "注射針34G", "ナノパスニードル34G",
        ],
        "手術材料": [
            "11番メス", "15番メス", "3-0PDFクリア", "4-0PDSクリア",
            "4-0青ナイロン", "5-0青ナイロン", "エルプ付糸ナイロン青",
            "穴あきドレープ", "穴無しドレープ",
            "トレパン1.5mm", "トレパン2mm", "トレパン3mm",
            "トレパン4mm", "トレパン5mm", "トレパン6mm",
        ],
        "検査": [
            "病理容器(空)", "病理容器(ホルマリン)", "培養スワブ",
            "病理細菌依頼用紙", "検鏡用スライドガラス", "検鏡用カバーガラス",
            "検鏡用ズーム液", "採血スピッツ生化", "採血スピッツ血糖", "採血スピッツ血算",
        ],
        "医療備品": [
            "シリンジ1ml中口", "シリンジ1mlロック", "シリンジ2.5ml中口",
            "シリンジ2.5mlロック", "シリンジ5ml中口", "シリンジ10ml中口",
            "シリンジ30ml中口", "滅菌ガーゼ10×10", "滅菌ガーゼ5×5",
            "不織布ガーゼ25×25", "滅菌手袋5.5", "滅菌手袋6", "滅菌手袋6.5",
            "二トリルグローブSS", "二トリルグローブS", "二トリルグローブM",
            "二トリルグローブL", "プラグローブS", "プラグローブM",
            "絆創膏", "ショットパッチS", "ショットパッチM",
            "弾包4号", "防水シーツ", "不織布ピローシート", "カミソリ10本入20P",
        ],
        "ピアス": [
            "R104TL", "R102TL", "R200TLY", "R200 TL", "7RF506CL", "ピアス消毒",
        ],
    }

    for category, names in items_data.items():
        for idx, name in enumerate(names):
            item = Item(
                name=name,
                category=category,
                par_level=5,
                unit="個",
                sort_order=idx,
            )
            db.session.add(item)
            db.session.flush()
            stock = Stock(item_id=item.id, quantity=0)
            db.session.add(stock)

    db.session.commit()


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
