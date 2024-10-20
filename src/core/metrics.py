import boto3
from botocore.config import Config
from datetime import datetime, timedelta
import statistics
from typing import List, Dict, Tuple, Any, Optional
import logging
from logger import logger

DEFAULT = "default"

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SpikeDetector:
    def __init__(self, profile_name: str = DEFAULT):
        logger.info(f"Initializing SpikeDetector with profile: {profile_name}")
        self.session = boto3.Session(profile_name=profile_name)
        self.cloudwatch = self.session.client(
            "cloudwatch",
            config=Config(retries={"max_attempts": 10, "mode": "standard"}),
        )

    def list_metrics(self) -> List[Dict[str, Any]]:
        """List all available CloudWatch metrics in the account."""
        logger.info("Listing all CloudWatch metrics")

        metrics = []
        paginator = self.cloudwatch.get_paginator("list_metrics")

        for page in paginator.paginate():
            metrics.extend(page["Metrics"])

        logger.info(f"Found {len(metrics)} metrics")
        return metrics

    def get_metric_data(
        self,
        namespace: str,
        metric_name: str,
        dimensions: List[Dict[str, str]],
        start_time: datetime,
        end_time: datetime,
        period: int = 300,
    ) -> List[float]:
        """Retrieve metric data for a given time range."""

        logger.info(f"Retrieving metric data for {namespace}:{metric_name}")

        response = self.cloudwatch.get_metric_data(
            MetricDataQueries=[
                {
                    "Id": "m1",
                    "MetricStat": {
                        "Metric": {
                            "Namespace": namespace,
                            "MetricName": metric_name,
                            "Dimensions": dimensions,
                        },
                        "Period": period,
                        "Stat": "Average",
                    },
                }
            ],
            StartTime=start_time,
            EndTime=end_time,
        )
        data = response["MetricDataResults"][0]["Values"]
        logger.info(f"Retrieved {len(data)} data points")
        return data

    def detect_spikes(
        self, data: List[float], threshold: float = 2
    ) -> List[Tuple[int, float]]:
        """Detect spikes in the metric data using z-score."""
        logger.info(f"Detecting spikes with threshold {threshold}")
        if not data:
            logger.warning("No data points to analyze")
            return []

        mean = statistics.mean(data)
        stdev = statistics.stdev(data) if len(data) > 1 else 0

        spikes = []
        for i, value in enumerate(data):
            if stdev > 0:
                z_score = (value - mean) / stdev
                if abs(z_score) > threshold:
                    spikes.append((i, value))

        if len(spikes) > 0:
            logger.info(f"Detected {len(spikes)} spikes")

        return spikes

    def scan_account(
        self,
        start_time: datetime,
        end_time: datetime,
        threshold: float = 2,
        sort_key: Optional[str] = None,
        sort_val: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Scan the entire account for spikes in all metrics."""
        logger.info(f"Scanning account for spikes from {start_time} to {end_time}")
        metrics = self.list_metrics()
        report = []

        for i, metric in enumerate(metrics):
            namespace = metric["Namespace"]
            metric_name = metric["MetricName"]
            dimensions = metric["Dimensions"]

            # for dim in
            if sort_key and not any(dim["Name"] == sort_key for dim in dimensions):
                continue
            if sort_val and not any(dim["Value"] == sort_val for dim in dimensions):
                continue

            logger.info(
                f"Analyzing metric {i+1}/{len(metrics)}: {namespace}:{metric_name}"
            )
            data = self.get_metric_data(
                namespace, metric_name, dimensions, start_time, end_time
            )
            spikes = self.detect_spikes(data, threshold)

            if spikes:
                report.append(
                    {
                        "Namespace": namespace,
                        "MetricName": metric_name,
                        "Dimensions": dimensions,
                        "Spikes": spikes,
                    }
                )

        logger.info(f"Scan complete. Found spikes in {len(report)} metrics")
        return report

    def generate_report(
        self,
        start_time: datetime,
        end_time: datetime,
        threshold: float = 2,
        sort_key: Optional[str] = None,
        sort_val: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Generate a report of detected spikes across the account."""
        logger.info("Generating spike detection report")
        report = self.scan_account(start_time, end_time, threshold, sort_key, sort_val)

        print(f"Spike Detection Report")
        print(f"Start Time: {start_time}")
        print(f"End Time: {end_time}")
        print(f"Threshold: {threshold} standard deviations\n")
        print(f"sortkey: {sort_key} sortval: {sort_val}\n")

        for item in report:
            print(f"Namespace: {item['Namespace']}")
            print(f"Metric Name: {item['MetricName']}")
            print(f"Dimensions: {item['Dimensions']}")
            print("Spikes:")
            for spike in item["Spikes"]:
                print(f"  - Index: {spike[0]}, Value: {spike[1]}")
            print()

        logger.info("Report generation complete")
        return report
