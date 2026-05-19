#!/bin/bash
# Elastic Beanstalk 배포 후 데이터 다운로드 (1회)
cd /var/app/current
python fetch_data.py || echo "Data fetch failed, will retry on next deploy"
