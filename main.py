
import sys
from modules.robot_controller import HumanoidRobot
from utils.logger import get_logger

log = get_logger("main")


def main() -> None:
    log.info("=" * 60)
    log.info("  Humanoid Robotic Head  —  NIT Jamshedpur")
    log.info("  Developer : Ranjeet Kumar Gupta")
    log.info("  Mentor    : Dr. Vijay Kumar Dalla")
    log.info("=" * 60)

    try:
        robot = HumanoidRobot()
        robot.run()
    except EnvironmentError as exc:
        log.critical("Environment error: %s", exc)
        sys.exit(1)
    except Exception as exc:
        log.critical("Fatal error: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
