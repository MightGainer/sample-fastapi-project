# type: ignore

import inspect
import threading
from functools import wraps
from typing import Any, Callable, Dict, Type, TypeVar, Union

from fastapi import Request

T = TypeVar('T')


class ServiceCollection:
    def __init__(self):
        self._services: Dict[Type, Dict[str, Any]] = {}
        self._singletons: Dict[Type, Any] = {}

    def add_transient(self, service_type: Type[T], implementation: Union[Type[T], Callable[[], T]]) -> None:
        self._validate_and_add(service_type, implementation, 'transient')

    def add_singleton(self, service_type: Type[T], implementation: Union[Type[T], Callable[[], T], T]) -> None:
        self._validate_and_add(service_type, implementation, 'singleton')

    def add_scoped(self, service_type: Type[T], implementation: Union[Type[T], Callable[[], T]]) -> None:
        self._validate_and_add(service_type, implementation, 'scoped')

    def _validate_and_add(
        self, service_type: Type[T], implementation: Union[Type[T], Callable[[], T], T], lifetime: str
    ) -> None:
        if service_type in self._services:
            raise Exception(f"Service type {service_type} already registered "
                            + "with implementation {self._services[service_type]['implementation']}")
        self._services[service_type] = {
            'implementation': implementation,
            'lifetime': lifetime
        }

    def build_service_provider(self) -> 'ServiceProvider':
        return ServiceProvider(self._services, self._singletons)


class ServiceProvider:
    def __init__(self, services: Dict[Type, Dict[str, Any]], singletons: Dict[Type, Any]):
        self._services = services
        self._singletons = singletons
        self._scopes = threading.local()

    def create_scope(self) -> 'ServiceScope':
        scope = ServiceScope(self)
        if not hasattr(self._scopes, 'current'):
            self._scopes.current = []
        self._scopes.current.append(scope)
        return scope

    async def get_service(self, service_type: Type[T]) -> T:
        if service_type not in self._services:
            raise Exception(f"Service of type {service_type} is not registered")

        service_info = self._services[service_type]
        if service_info['lifetime'] == 'singleton':
            if service_type not in self._singletons:
                self._singletons[service_type] = await self._create_implementation(service_info['implementation'])
            return self._singletons[service_type]
        elif service_info['lifetime'] == 'scoped':
            current_scope = self._get_current_scope()
            if current_scope is None:
                raise Exception("No active scope found for scoped service")
            return await current_scope.get_service(service_type)

        return await self._create_implementation(service_info['implementation'])

    async def _create_implementation(self, implementation: Union[Type[T], Callable[[], T], T]) -> T:
        if callable(implementation):
            if inspect.isclass(implementation):
                constructor = inspect.signature(implementation.__init__)
                dependencies = {param.name: await self.get_service(param.annotation)
                                for param in constructor.parameters.values()
                                if param.name != 'self' and param.annotation != param.empty}
                return implementation(**dependencies)
            else:
                if inspect.iscoroutinefunction(implementation):
                    return await implementation()
                else:
                    return implementation()
        return implementation

    def _get_current_scope(self) -> 'ServiceScope':
        if not hasattr(self._scopes, 'current') or not self._scopes.current:
            return None
        return self._scopes.current[-1]

    def injector(self) -> Callable:
        def decorator(func_or_class: Any) -> Any:
            if inspect.isclass(func_or_class):
                return self._inject_class(func_or_class)
            else:
                return self._inject_function(func_or_class)

        return decorator

    def _inject_function(self, func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            sig = inspect.signature(func)
            for param in sig.parameters.values():
                if (
                    param.name not in kwargs
                    and param.default == inspect.Parameter.empty
                    and param.annotation != Request
                ):
                    try:
                        service = await self.get_service(param.annotation)
                        kwargs[param.name] = service
                    except Exception:
                        raise
            return await func(*args, **kwargs)

        return wrapper

    def _inject_class(self, cls: Type[Any]) -> Type[Any]:
        original_init = cls.__init__

        @wraps(original_init)
        async def new_init(self, *args: Any, **kwargs: Any) -> None:
            sig = inspect.signature(original_init)
            for param in sig.parameters.values():
                if (
                    param.name not in kwargs
                    and param.default == inspect.Parameter.empty
                    and param.annotation != Request
                ):
                    try:
                        service = await self.get_service(param.annotation)
                        kwargs[param.name] = service
                    except Exception:
                        raise
            await original_init(self, *args, **kwargs)

        cls.__init__ = new_init

        return cls


class ServiceScope:
    def __init__(self, service_provider: ServiceProvider):
        self._service_provider = service_provider
        self._scoped_services: Dict[Type, Any] = {}

    def get_service(self, service_type: Type[T]) -> T:
        if service_type not in self._scoped_services:
            service_info = self._service_provider._services[service_type]
            if service_info['lifetime'] == 'scoped':
                implementation = self._service_provider._create_implementation(service_info['implementation'])
                self._scoped_services[service_type] = implementation
                return implementation
        return self._scoped_services[service_type]

    def dispose(self) -> None:
        for service in self._scoped_services.values():
            if hasattr(service, 'dispose'):
                service.dispose()
        self._scoped_services.clear()
        if hasattr(self._service_provider._scopes, 'current'):
            self._service_provider._scopes.current.pop()


if __name__ == "__main__":
    # Example services
    class IService:
        def do_something(self) -> None:
            pass

    class ConcreteServiceA(IService):
        def do_something(self) -> None:
            print("Service A doing something")

    class ConcreteServiceB:
        def __init__(self, service: IService) -> None:
            self.service = service

        def do_something_else(self) -> None:
            print("Service B doing something else")
            self.service.do_something()

    # Scoped service example
    class IScopedService:
        def do_scoped_work(self) -> None:
            pass

    class ConcreteScopedService(IScopedService):
        def __init__(self):
            print("ConcreteScopedService created")

        def do_scoped_work(self) -> None:
            print("Doing scoped work")

        def dispose(self) -> None:
            print("ConcreteScopedService disposed")

    # Usage
    service_collection = ServiceCollection()
    service_collection.add_transient(IService, ConcreteServiceA)
    service_collection.add_singleton(ConcreteServiceB, ConcreteServiceB)
    service_collection.add_scoped(IScopedService, ConcreteScopedService)

    service_provider = service_collection.build_service_provider()

    @service_provider.injector()
    def some_function(service: IService, scoped_service: IScopedService) -> None:
        service.do_something()
        scoped_service.do_scoped_work()

    @service_provider.injector()
    def another_function(service_b: ConcreteServiceB) -> None:
        service_b.do_something_else()

    @service_provider.injector()
    class SomeClass:
        def __init__(self, service: IService, scoped_service: IScopedService) -> None:
            self.service = service
            self.scoped_service = scoped_service

        def method(self) -> None:
            self.service.do_something()
            self.scoped_service.do_scoped_work()

    # Create a new scope
    scope = service_provider.create_scope()
    try:
        some_function()  # This should print "Service A doing something" and "Doing scoped work"
        another_function()  # This should print "Service B doing something else" and "Service A doing something"

        some_class_instance = SomeClass()
        some_class_instance.method()  # This should print "Service A doing something" and "Doing scoped work"
    finally:
        scope.dispose()  # This should print "ConcreteScopedService disposed"
