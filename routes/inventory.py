import os
import uuid

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

from models import Area, Item, Stock, db

inventory_bp = Blueprint("inventory", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _get_areas():
    return Area.query.order_by(Area.sort_order, Area.name).all()


def _get_categories():
    rows = db.session.query(Item.category).distinct().order_by(Item.category).all()
    return [c[0] for c in rows]


@inventory_bp.route("/inventory")
def inventory_list():
    category = request.args.get("category", "")
    status = request.args.get("status", "")
    q = request.args.get("q", "")

    query = Item.query.order_by(Item.category, Item.sort_order, Item.name)
    if category:
        query = query.filter(Item.category == category)
    if q:
        query = query.filter(Item.name.contains(q))

    items = query.all()

    if status:
        items = [i for i in items if i.status == status]

    return render_template(
        "inventory.html",
        items=items,
        categories=_get_categories(),
        selected_category=category,
        selected_status=status,
        search_query=q,
    )


@inventory_bp.route("/items/manage")
def item_manage():
    category = request.args.get("category", "")
    query = Item.query.order_by(Item.category, Item.sort_order, Item.name)
    if category:
        query = query.filter(Item.category == category)
    items = query.all()

    return render_template(
        "item_manage.html",
        items=items,
        categories=_get_categories(),
        selected_category=category,
    )


@inventory_bp.route("/items/add", methods=["GET", "POST"])
def item_add():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        formal_name = request.form.get("formal_name", "").strip()
        category = request.form.get("category", "").strip()
        par_level = int(request.form.get("par_level", 0))
        unit = request.form.get("unit", "個").strip()
        area = request.form.get("area", "").strip()
        supplier = request.form.get("supplier", "").strip()

        image_path = ""
        file = request.files.get("image")
        if file and file.filename and allowed_file(file.filename):
            ext = file.filename.rsplit(".", 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            image_path = f"images/{filename}"

        item = Item(
            name=name,
            formal_name=formal_name,
            category=category,
            par_level=par_level,
            unit=unit,
            area=area,
            supplier=supplier,
            image_path=image_path,
        )
        db.session.add(item)
        db.session.flush()

        stock = Stock(item_id=item.id, quantity=0)
        db.session.add(stock)
        db.session.commit()

        flash(f"「{name}」を追加しました！", "success")
        return redirect(url_for("inventory.item_manage"))

    return render_template(
        "item_form.html",
        item=None,
        categories=_get_categories(),
        areas=_get_areas(),
    )


@inventory_bp.route("/items/<int:item_id>/edit", methods=["GET", "POST"])
def item_edit(item_id):
    item = Item.query.get_or_404(item_id)

    if request.method == "POST":
        item.name = request.form.get("name", "").strip()
        item.formal_name = request.form.get("formal_name", "").strip()
        item.category = request.form.get("category", "").strip()
        item.par_level = int(request.form.get("par_level", 0))
        item.unit = request.form.get("unit", "個").strip()
        item.area = request.form.get("area", "").strip()
        item.supplier = request.form.get("supplier", "").strip()

        file = request.files.get("image")
        if file and file.filename and allowed_file(file.filename):
            if item.image_path:
                old_path = os.path.join(current_app.config["UPLOAD_FOLDER"], os.path.basename(item.image_path))
                if os.path.exists(old_path):
                    os.remove(old_path)
            ext = file.filename.rsplit(".", 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            item.image_path = f"images/{filename}"

        db.session.commit()
        flash(f"「{item.name}」を更新しました！", "success")
        return redirect(url_for("inventory.item_manage"))

    return render_template(
        "item_form.html",
        item=item,
        categories=_get_categories(),
        areas=_get_areas(),
    )


@inventory_bp.route("/items/<int:item_id>/delete-image", methods=["POST"])
def item_delete_image(item_id):
    item = Item.query.get_or_404(item_id)
    if item.image_path:
        old_path = os.path.join(current_app.config["UPLOAD_FOLDER"], os.path.basename(item.image_path))
        if os.path.exists(old_path):
            os.remove(old_path)
        item.image_path = ""
        db.session.commit()
        flash("画像を削除しました", "success")
    return redirect(url_for("inventory.item_edit", item_id=item.id))


@inventory_bp.route("/items/<int:item_id>/delete", methods=["POST"])
def item_delete(item_id):
    item = Item.query.get_or_404(item_id)
    if item.image_path:
        old_path = os.path.join(current_app.config["UPLOAD_FOLDER"], os.path.basename(item.image_path))
        if os.path.exists(old_path):
            os.remove(old_path)
    name = item.name
    db.session.delete(item)
    db.session.commit()
    flash(f"「{name}」を削除しました", "danger")
    return redirect(url_for("inventory.item_manage"))


@inventory_bp.route("/items/reorder", methods=["POST"])
def item_reorder():
    order_data = request.form.getlist("item_order")
    for idx, item_id in enumerate(order_data):
        item = Item.query.get(int(item_id))
        if item:
            item.sort_order = idx
    db.session.commit()
    return redirect(url_for("inventory.item_manage"))


# ===== Area Management =====

@inventory_bp.route("/areas")
def area_list():
    areas = _get_areas()
    return render_template("area_manage.html", areas=areas)


@inventory_bp.route("/areas/add", methods=["POST"])
def area_add():
    name = request.form.get("name", "").strip()
    if name and not Area.query.filter_by(name=name).first():
        area = Area(name=name)
        db.session.add(area)
        db.session.commit()
    return redirect(url_for("inventory.area_list"))


@inventory_bp.route("/areas/<int:area_id>/edit", methods=["POST"])
def area_edit(area_id):
    area = Area.query.get_or_404(area_id)
    old_name = area.name
    new_name = request.form.get("name", "").strip()
    if new_name and new_name != old_name:
        area.name = new_name
        # Update all items with old area name
        for item in Item.query.filter_by(area=old_name).all():
            item.area = new_name
        db.session.commit()
    return redirect(url_for("inventory.area_list"))


@inventory_bp.route("/areas/<int:area_id>/delete", methods=["POST"])
def area_delete(area_id):
    area = Area.query.get_or_404(area_id)
    # Clear area from items
    for item in Item.query.filter_by(area=area.name).all():
        item.area = ""
    db.session.delete(area)
    db.session.commit()
    return redirect(url_for("inventory.area_list"))
