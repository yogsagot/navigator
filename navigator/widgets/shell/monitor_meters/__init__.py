"""The meters inside Utilities > System monitor: the processors, the memory and the sensors."""

from navigator.widgets.shell.monitor_meters.monitor_meters import (
    CpuMeters, MemoryMeters, SensorList, SensorRow, cpu_layout, memory_width, sensor_rows,
)

__all__ = ["CpuMeters", "MemoryMeters", "SensorList", "SensorRow", "cpu_layout", "memory_width", "sensor_rows"]
