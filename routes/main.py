from flask import Blueprint, flash, redirect, render_template, request, url_for

from models import BoardMessage, Item, Staff, db

main_bp = Blueprint("main", __name__)


@main_bp.route("/health")
def health():
    return "ok", 200


@main_bp.route("/")
def index():
    items = Item.query.all()
    order_needed = [i for i in items if i.status == "order"]
    low_items = [i for i in items if i.status == "low"]
    normal_items = [i for i in items if i.status == "normal"]
    total = len(items)

    messages = BoardMessage.query.order_by(BoardMessage.created_at.desc()).limit(30).all()
    staffs = Staff.query.order_by(Staff.sort_order, Staff.name).all()

    return render_template(
        "index.html",
        order_needed=order_needed,
        low_items=low_items,
        normal_count=len(normal_items),
        low_count=len(low_items),
        order_count=len(order_needed),
        total=total,
        messages=messages,
        staffs=staffs,
    )


@main_bp.route("/board/post", methods=["POST"])
def board_post():
    author = request.form.get("author", "").strip()
    body = request.form.get("body", "").strip()
    if author and body:
        msg = BoardMessage(author=author, body=body)
        db.session.add(msg)
        db.session.commit()
        flash("メッセージを投稿しました！", "success")
    return redirect(url_for("main.index") + "#board")


@main_bp.route("/board/<int:msg_id>/delete", methods=["POST"])
def board_delete(msg_id):
    msg = BoardMessage.query.get_or_404(msg_id)
    db.session.delete(msg)
    db.session.commit()
    flash("メッセージを削除しました", "danger")
    return redirect(url_for("main.index") + "#board")
