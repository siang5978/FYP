from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from CTFd.plugins import register_plugin_assets_directory
from CTFd.models import db, Solves
from CTFd.utils.user import get_current_user
from CTFd.utils.decorators import admins_only, authed_only
from .models import Achievement, AchievementChallenge


def load(app):
    register_plugin_assets_directory(app, base_path='/plugins/achievement_plugin/assets')

    with app.app_context():
        db.create_all()

    achievement_bp = Blueprint(
        "achievement_plugin",
        __name__,
        template_folder="templates"
    )

    from CTFd.models import Challenges

    @achievement_bp.route("/admin/achievements/create", methods=["GET", "POST"])
    @admins_only
    def create_achievements():
        if request.method == "POST":
            name = request.form.get("name")
            description = request.form.get("description")
            visible = request.form.get("visible")
            dependent_challenges = request.form.getlist("dependent_challenges")

            if not name:
                flash("Achievement name is required", "danger")
                return redirect(url_for("achievement_plugin.create_achievements"))

            achievement = Achievement(name=name, description=description, visible=visible)
            db.session.add(achievement)
            db.session.commit()

            for cid in dependent_challenges:
                ac = AchievementChallenge(achievement_id=achievement.id, challenge_id=int(cid))
                db.session.add(ac)
            db.session.commit()

            flash("Achievement created successfully!", "success")
            return redirect(url_for("achievement_plugin.admin_view_achievements"))  

        challenges = Challenges.query.all()
        return render_template("admin/create.html", challenges=challenges)

    @achievement_bp.route("/admin/achievements/<int:achievement_id>", methods=["GET", "POST"])
    @admins_only
    def achievement_detail(achievement_id):
        achievement = Achievement.query.get(achievement_id)
        if not achievement:
            flash("Achievement not found", "danger")
            return redirect(url_for("achievement_plugin.admin_view_achievements"))

        all_challenges = Challenges.query.all()
        dep_challenges = AchievementChallenge.query.filter_by(achievement_id=achievement_id).all()
        selected_challenge_ids = [ac.challenge_id for ac in dep_challenges]

        if request.method == "POST":
            achievement.name = request.form.get("name")
            achievement.description = request.form.get("description")
            achievement.visible = request.form.get("visible")
            db.session.commit()

            new_cids = [int(cid) for cid in request.form.getlist("dependent_challenges")]
            AchievementChallenge.query.filter_by(achievement_id=achievement.id).delete()
            db.session.commit()

            for cid in new_cids:
                ac = AchievementChallenge(achievement_id=achievement.id, challenge_id=cid)
                db.session.add(ac)
            db.session.commit()

            flash("Achievement updated successfully!", "success")
            return redirect(url_for("achievement_plugin.admin_view_achievements")) 

        return render_template(
            "admin/update.html",
            achievement=achievement,
            all_challenges=all_challenges,
            selected_challenge_ids=selected_challenge_ids
        )

    @achievement_bp.route("/achievements", methods=["GET"])
    @authed_only
    def user_view_achievements():
        user = get_current_user()
        all_achievements = Achievement.query.filter_by(visible="Visible").all()
        earned_ids = set()
        achievements_progress = {}

        for ach in all_achievements:

            challenge_ids = [
                ac.challenge_id
                for ac in AchievementChallenge.query.filter_by(achievement_id=ach.id).all()
            ]

            total = len(challenge_ids)

            if total == 0:
                earned_ids.add(ach.id)
                achievements_progress[ach.id] = {"completed": 0, "total": 0}
                continue

            solved_count = Solves.query.filter(
                Solves.user_id == user.id,
                Solves.challenge_id.in_(challenge_ids)
            ).count()

            if solved_count == total:
                earned_ids.add(ach.id)

            achievements_progress[ach.id] = {"completed": solved_count, "total": total}

        return render_template(
            "user/achievements.html",
            achievements=all_achievements,
            earned=earned_ids,
            progress=achievements_progress
        )

    @achievement_bp.route("/api/v1/achievements/<int:achievement_id>", methods=["DELETE"])
    @admins_only
    def delete_achievement(achievement_id):
        achievement = Achievement.query.get(achievement_id)
        if not achievement:
            return jsonify({"success": False, "message": "Achievement not found"}), 404

        try:
            AchievementChallenge.query.filter_by(achievement_id=achievement_id).delete()
            db.session.delete(achievement)
            db.session.commit()
            return jsonify({"success": True, "message": f"Achievement '{achievement.name}' and its dependencies deleted"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": f"Error deleting achievement: {str(e)}"}), 500

    @achievement_bp.route("/admin/achievements", methods=["GET"])
    @admins_only
    def admin_view_achievements():
        from CTFd.models import Challenges

        achievements = Achievement.query.all()
        achievements_info = []

        for ach in achievements:
            dep_challenges = AchievementChallenge.query.filter_by(achievement_id=ach.id).all()
            challenge_names = []
            for ac in dep_challenges:
                challenge = Challenges.query.get(ac.challenge_id)
                if challenge:
                    challenge_names.append(challenge.name)

            achievements_info.append({
                "id": ach.id,
                "name": ach.name,
                "description": ach.description,
                "visible": ach.visible,
                "dependent_challenges": challenge_names
            })

        return render_template(
            "admin/achievements.html",
            achievements=achievements_info
        )

    app.register_blueprint(achievement_bp)
