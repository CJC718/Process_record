import glob
from ui.parser import *  ##使用Lidar点云自带ring值
## from ui.parser_cal import * ##使用角度计算的方式获取ring值
from tqdm import tqdm
from cyber_record.record import Record
import time
import subprocess
import argparse


def main(input_path, out_path):
    start_time = time.time()

    pcd_out_directory = os.path.join(out_path, "pcd")
    os.makedirs(pcd_out_directory, exist_ok=True)
    image_out_directory = os.path.join(out_path, "image")
    os.makedirs(image_out_directory, exist_ok=True)

    record_files = glob.glob(os.path.join(input_path, "record", "*.record.*"))
    video_files = glob.glob(os.path.join(input_path, "video", "*.264"))
    total_messages = sum(1 for _ in Record(record_files[0]).read_messages())

    pointcloud_parser = PointCloudParser(pcd_out_directory)

    progress_bar = tqdm(total=total_messages, desc="Processing Lidar messages")

    for record_file in record_files:
        record = Record(record_file)
        for message in record.read_messages():
            topic, msg, t = message
            if topic == "omnisense/lidar/PointCloud":
                pointcloud_parser.parse(msg)

            progress_bar.update(1)

    progress_bar.close()
    end_time = time.time()
    execution_time = end_time - start_time
    print("Process Lidar Time cost:", execution_time, "s")

    # 输入视频文件名和输出图像文件名前缀
    video_file = video_files[0]
    output_image_prefix = image_out_directory + "/image_"

    # 使用ffmpeg解码视频并保存图像
    command = [
        "ffmpeg",
        "-i", video_file,
        "-vf", "fps=10",  # 选择帧率，此处为每秒保存10帧，可以根据需要调整
        f"{output_image_prefix}%04d.jpg"  # 输出图像文件名格式，%04d表示使用四位数字作为文件名序号
    ]

    try:
        subprocess.run(command, check=True)
        video_time = time.time()
        print("视频帧已成功保存为JPEG图像文件, 共花费时间：", video_time - end_time)
    except subprocess.CalledProcessError as e:
        print("处理过程中出现错误:", e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process Lidar data and extract video frames.")
    parser.add_argument("--input", required=True, help="Input path containing record and video directories.")
    parser.add_argument("--output", required=True, help="Output path for saving processed data.")
    args = parser.parse_args()

    if not os.path.exists(args.output):
        os.makedirs(args.output)

    main(args.input, args.output)
