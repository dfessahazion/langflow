import importlib
import inspect

from loguru import logger
from sqlmodel import Session, select

from langflow_base.services.auth.utils import create_super_user, verify_password
from langflow_base.services.database.utils import initialize_database
from langflow_base.services.factory import ServiceFactory
from langflow_base.services.manager import service_manager
from langflow_base.services.schema import ServiceType
from langflow_base.services.settings.constants import DEFAULT_SUPERUSER, DEFAULT_SUPERUSER_PASSWORD
from langflow_base.services.socket.utils import set_socketio_server

from .deps import get_db_service, get_session, get_settings_service


def get_factories():
    service_names = [ServiceType(service_type).value.replace("_service", "") for service_type in ServiceType]
    base_module = "langflow.services"
    factories = []

    for name in service_names:
        try:
            module_name = f"{base_module}.{name}.factory"
            module = importlib.import_module(module_name)

            # Find all classes in the module that are subclasses of ServiceFactory
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, ServiceFactory) and obj is not ServiceFactory:
                    factories.append(obj())
                    break

        except Exception as exc:
            logger.exception(exc)
            raise RuntimeError(f"Could not initialize services. Please check your settings. Error in {name}.") from exc

    return factories


def get_or_create_super_user(session: Session, username, password, is_default):
    from langflow_base.services.database.models.user.model import User

    user = session.exec(select(User).where(User.username == username)).first()

    if user and user.is_superuser:
        return None  # Superuser already exists

    if user and is_default:
        if user.is_superuser:
            if verify_password(password, user.password):
                return None
            else:
                # Superuser exists but password is incorrect
                # which means that the user has changed the
                # base superuser credentials.
                # This means that the user has already created
                # a superuser and changed the password in the UI
                # so we don't need to do anything.
                logger.debug(
                    "Superuser exists but password is incorrect. "
                    "This means that the user has changed the "
                    "base superuser credentials."
                )
                return None
        else:
            logger.debug("User with superuser credentials exists but is not a superuser.")
            return None

    if user:
        if verify_password(password, user.password):
            raise ValueError("User with superuser credentials exists but is not a superuser.")
        else:
            raise ValueError("Incorrect superuser credentials")

    if is_default:
        logger.debug("Creating default superuser.")
    else:
        logger.debug("Creating superuser.")
    try:
        return create_super_user(username, password, db=session)
    except Exception as exc:
        if "UNIQUE constraint failed: user.username" in str(exc):
            # This is to deal with workers running this
            # at startup and trying to create the superuser
            # at the same time.
            logger.debug("Superuser already exists.")
            return None


def setup_superuser(settings_service, session: Session):
    if settings_service.auth_settings.AUTO_LOGIN:
        logger.debug("AUTO_LOGIN is set to True. Creating default superuser.")
    else:
        # Remove the default superuser if it exists
        teardown_superuser(settings_service, session)

    username = settings_service.auth_settings.SUPERUSER
    password = settings_service.auth_settings.SUPERUSER_PASSWORD

    is_default = (username == DEFAULT_SUPERUSER) and (password == DEFAULT_SUPERUSER_PASSWORD)

    try:
        user = get_or_create_super_user(session=session, username=username, password=password, is_default=is_default)
        if user is not None:
            logger.debug("Superuser created successfully.")
    except Exception as exc:
        logger.exception(exc)
        raise RuntimeError("Could not create superuser. Please create a superuser manually.") from exc
    finally:
        settings_service.auth_settings.reset_credentials()


def teardown_superuser(settings_service, session):
    """
    Teardown the superuser.
    """
    # If AUTO_LOGIN is True, we will remove the default superuser
    # from the database.

    if not settings_service.auth_settings.AUTO_LOGIN:
        try:
            logger.debug("AUTO_LOGIN is set to False. Removing default superuser if exists.")
            username = DEFAULT_SUPERUSER
            from langflow_base.services.database.models.user.model import User

            user = session.exec(select(User).where(User.username == username)).first()
            if user and user.is_superuser is True:
                session.delete(user)
                session.commit()
                logger.debug("Default superuser removed successfully.")
            else:
                logger.debug("Default superuser not found.")
        except Exception as exc:
            logger.exception(exc)
            raise RuntimeError("Could not remove default superuser.") from exc


def teardown_services():
    """
    Teardown all the services.
    """
    try:
        teardown_superuser(get_settings_service(), next(get_session()))
    except Exception as exc:
        logger.exception(exc)
    try:
        service_manager.teardown()
    except Exception as exc:
        logger.exception(exc)


def initialize_settings_service():
    """
    Initialize the settings manager.
    """
    from langflow_base.services.settings import factory as settings_factory

    service_manager.register_factory(settings_factory.SettingsServiceFactory())


def initialize_session_service():
    """
    Initialize the session manager.
    """
    from langflow_base.services.cache import factory as cache_factory
    from langflow_base.services.session import factory as session_service_factory  # type: ignore

    initialize_settings_service()

    service_manager.register_factory(
        cache_factory.CacheServiceFactory(),
    )

    service_manager.register_factory(
        session_service_factory.SessionServiceFactory(),
    )


def initialize_services(fix_migration: bool = False, socketio_server=None):
    """
    Initialize all the services needed.
    """
    for factory in get_factories():
        try:
            service_manager.register_factory(factory)
        except Exception as exc:
            logger.exception(exc)
            raise RuntimeError("Could not initialize services. Please check your settings.") from exc

    # Test cache connection
    service_manager.get(ServiceType.CACHE_SERVICE)
    # Setup the superuser
    try:
        initialize_database(fix_migration=fix_migration)
    except Exception as exc:
        logger.error(exc)
        raise exc
    setup_superuser(service_manager.get(ServiceType.SETTINGS_SERVICE), next(get_session()))
    try:
        get_db_service().migrate_flows_if_auto_login()
    except Exception as exc:
        logger.error(f"Error migrating flows: {exc}")
        raise RuntimeError("Error migrating flows") from exc

    # Initialize the SocketIO service
    set_socketio_server(socketio_server)