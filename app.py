# app.py

from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import date, timedelta
from collections import defaultdict
import os
from extensions import db
from models import Report


def create_app():
    """
    Flaskアプリケーションを作成するファクトリ関数
    """
    app = Flask(__name__)

    # データベース設定
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'site.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # データベースインスタンスをアプリケーションに紐づける
    db.init_app(app)
    
    # データを保存する前に整形するヘルパー関数
    def clean_input(text):
        if not text:
            return None
        lines = [line.strip() for line in text.split('\n') if line.strip() and line.strip() != '・']
        if not lines:
            return None
        return '\n'.join(lines)

    # --- ルート（URLと関数の紐づけ）の定義 ---

    @app.route('/')
    def index():
        """トップページ：日報の一覧を表示"""
        reports = Report.query.order_by(Report.date.desc()).all()
        return render_template('index.html', reports=reports)

    @app.route('/report')
    def report_form():
        """日報入力フォームを表示"""
        return render_template('report_form.html')

    @app.route('/submit', methods=['POST'])
    def submit_report():
        """フォームから送信された日報をデータベースに保存"""
        if request.method == 'POST':
            date_str = request.form['date']
            tasks = clean_input(request.form['tasks'])
            progress = clean_input(request.form['progress'])
            memo = clean_input(request.form['memo'])
            challenges = clean_input(request.form['challenges'])
            next_plan = clean_input(request.form['next_plan'])

            new_report = Report(
                date=date_str,
                tasks=tasks,
                progress=progress,
                memo=memo,
                challenges=challenges,
                next_plan=next_plan
            )

            db.session.add(new_report)
            db.session.commit()

            return redirect(url_for('index'))

        return redirect(url_for('report_form'))

    @app.route('/weekly-report')
    def weekly_report():
        """週報を表示（集計機能を含む）"""
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        weekly_reports = Report.query.filter(
            Report.date >= start_of_week.isoformat(),
            Report.date <= end_of_week.isoformat()
        ).order_by(Report.date.desc()).all()

        # 週報の集計ロジック
        all_tasks = []
        all_challenges = []
        all_next_plans = []
        
        for report in weekly_reports:
            if report.tasks:
                all_tasks.extend([t.strip() for t in report.tasks.split('\n') if t.strip()])
            if report.challenges:
                all_challenges.extend([c.strip() for c in report.challenges.split('\n') if c.strip()])
            if report.next_plan:
                all_next_plans.extend([p.strip() for p in report.next_plan.split('\n') if p.strip()])

        unique_tasks = sorted(list(set(all_tasks)))
        unique_challenges = sorted(list(set(all_challenges)))
        unique_next_plans = sorted(list(set(all_next_plans)))

        weekly_report_text = f"""
【週次報告：{start_of_week.strftime('%Y年%m月%d日')}〜{end_of_week.strftime('%Y年%m月%d日')}】

1. 今週の完了タスク
{'- ' + '\n- '.join(unique_tasks) if unique_tasks else '- 今週は完了したタスクがありません。'}

2. 課題
{'- ' + '\n- '.join(unique_challenges) if unique_challenges else '- 特になし'}

3. 翌週の予定
{'- ' + '\n- '.join(unique_next_plans) if unique_next_plans else '- 特になし'}
"""
        return render_template('weekly_report.html', reports=weekly_reports, weekly_report_text=weekly_report_text.strip())


    @app.route('/monthly-report')
    def monthly_report():
        """月報を表示（集計機能を含む）"""
        today = date.today()
        start_of_month = today.replace(day=1)
        if today.month == 12:
            end_of_month = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_of_month = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

        monthly_reports = Report.query.filter(
            Report.date >= start_of_month.isoformat(),
            Report.date <= end_of_month.isoformat()
        ).order_by(Report.date.desc()).all()

        # 月報の集計ロジック
        all_tasks = []
        all_challenges = []
        all_next_plans = []
        for report in monthly_reports:
            if report.tasks:
                all_tasks.extend([t.strip() for t in report.tasks.split('\n') if t.strip()])
            if report.challenges:
                all_challenges.extend([c.strip() for c in report.challenges.split('\n') if c.strip()])
            if report.next_plan:
                all_next_plans.extend([p.strip() for p in report.next_plan.split('\n') if p.strip()])
        
        # 重複を排除して、ユニークなタスク、課題、予定リストを作成
        unique_tasks = sorted(list(set(all_tasks)))
        unique_challenges = sorted(list(set(all_challenges)))
        unique_next_plans = sorted(list(set(all_next_plans)))

        # 報告書テンプレートの生成
        monthly_report_text = f"""
【月次報告：{start_of_month.strftime('%Y年%m月')}】

1. 完了タスク
{'- ' + '\n- '.join(unique_tasks) if unique_tasks else '- 今月は完了したタスクがありません。'}

2. 課題
{'- ' + '\n- '.join(unique_challenges) if unique_challenges else '- 特になし'}

3. 翌月の予定
{'- ' + '\n- '.join(unique_next_plans) if unique_next_plans else '- 特になし'}
"""
        # タスク出現回数の集計（ランキング用）
        task_counts = defaultdict(int)
        for report in monthly_reports:
            tasks = [task.strip() for task in report.tasks.split('\n') if task.strip()]
            for task in tasks:
                task_counts[task] += 1
        sorted_tasks = sorted(task_counts.items(), key=lambda item: item[1], reverse=True)

        return render_template('monthly_report.html', 
                            reports=monthly_reports, 
                            sorted_tasks=sorted_tasks,
                            monthly_report_text=monthly_report_text.strip())

    @app.route('/edit/<int:report_id>', methods=['GET', 'POST'])
    def edit_report(report_id):
        """日報の編集フォームを表示・更新"""
        report_to_edit = Report.query.get_or_404(report_id)

        if request.method == 'POST':
            report_to_edit.date = request.form['date']
            report_to_edit.tasks = clean_input(request.form['tasks'])
            report_to_edit.progress = clean_input(request.form['progress'])
            report_to_edit.memo = clean_input(request.form['memo'])
            report_to_edit.challenges = clean_input(request.form['challenges'])
            report_to_edit.next_plan = clean_input(request.form['next_plan'])

            db.session.commit()
            return redirect(url_for('index'))
        else:
            return render_template('edit_report.html', report=report_to_edit)

    @app.route('/delete/<int:report_id>')
    def delete_report(report_id):
        """日報を削除"""
        report_to_delete = Report.query.get_or_404(report_id)

        db.session.delete(report_to_delete)
        db.session.commit()

        return redirect(url_for('index'))

    @app.route('/generate_report/<int:report_id>')
    def generate_report(report_id):
        """ワンクリックで報告書を自動生成"""
        report_data = Report.query.get_or_404(report_id)

        report_template = f"""
本日の業務報告です。

【今日の作業内容】
{report_data.tasks}

【進捗状況】
{report_data.progress if report_data.progress else '本日中に完了しました。'}

【課題・対応中】
{report_data.challenges if report_data.challenges else '特になし'}

【明日以降の予定】
{report_data.next_plan if report_data.next_plan else '特になし'}

【所感・メモ】
{report_data.memo if report_data.memo else '特になし'}
"""
        return jsonify({'report_text': report_template.strip()})

    return app


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        # データベースを初期化し、テーブルを作成
        db.create_all()
    app.run(debug=True)
