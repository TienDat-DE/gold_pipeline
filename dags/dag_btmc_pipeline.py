from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import pendulum

# Cấu hình múi giờ Việt Nam (Quan trọng để Airflow chạy đúng giờ thực tế)
local_tz = pendulum.timezone("Asia/Ho_Chi_Minh")

default_args = {
    'owner': 'TienDat-DE',
    'depends_on_past': False,
    'email_on_failure': False, # Có thể cấu hình gửi mail báo lỗi sau
    'email_on_retry': False,
    'retries': 2, # Nếu web BTMC sập, Airflow sẽ tự thử lại 2 lần
    'retry_delay': timedelta(minutes=5), # Mỗi lần thử lại cách nhau 5 phút
}

with DAG(
    dag_id='btmc_gold_pipeline_daily',
    default_args=default_args,
    description='Luồng ETL lấy giá vàng BTMC hàng ngày',
    schedule_interval='0 10 * * *', # Chạy tự động vào 10:00 sáng mỗi ngày
    start_date=datetime(2026, 11, 1, tzinfo=local_tz),
    catchup=False, # Không chạy bù các ngày trong quá khứ lúc mới bật DAG
    tags=['gold_pipeline', 'btmc'],
) as dag:

    # ==============================================================================
    # LƯU Ý ĐƯỜNG DẪN: Cập nhật lại đường dẫn tuyệt đối tới thư mục Gold_pipeline 
    # trên máy Mac của bạn.
    # {{ ds_nodash }} là Macro của Airflow, tự động truyền ngày chạy (VD: 20261103)
    # ==============================================================================
    
    # Kịch bản: Di chuyển vào thư mục dự án -> Kích hoạt môi trường ảo -> Chạy Master
    run_btmc_master = BashOperator(
        task_id='trigger_master_pipeline',
        bash_command="""
        cd /Users/tsdeveloper/Desktop/Gold_Sentiment_Analysis/Gold_pipeline && \
        source venv/bin/activate && \
        python -m jobs.BTMC.job_btmc_master --date {{ ds_nodash }}
        """
    )

    # Nếu sau này có SJC, PNJ, DOJI, bạn chỉ cần khai báo thêm task và gom lại:
    # [run_btmc_master, run_sjc_master, run_pnj_master]

    run_btmc_master