from __future__ import annotations

from .loader import render_template


def render_entity(class_name: str) -> str:
    """Return the template for a domain entity."""
    return render_template("entity.py.j2", subfolder="domain", class_name=class_name)


def render_repository_interface(
    class_name: str,
    entity_name: str,
    entity_file: str,
    resource_folder: str,
    domain_module_base: str = "",
) -> str:
    """Return the template for a repository interface."""
    return render_template(
        "repository_interface.py.j2",
        subfolder="domain",
        class_name=class_name,
        entity_name=entity_name,
        entity_file=entity_file,
        resource_folder=resource_folder,
        domain_module_base=domain_module_base,
    )


def render_service_interface(
    class_name: str,
    domain_module_base: str = "",
    application_module_base: str = "",
) -> str:
    """Return the template for a service interface."""
    return render_template(
        "service_interface.py.j2",
        subfolder="application",
        class_name=class_name,
        domain_module_base=domain_module_base,
        application_module_base=application_module_base,
    )


def render_interactor(class_name: str, entity_name: str, entity_file: str) -> str:
    """Return the template for an interactor."""
    return render_template(
        "interactor.py.j2",
        subfolder="application",
        class_name=class_name,
        entity_name=entity_name,
        entity_file=entity_file,
    )


def render_mediator(class_name: str) -> str:
    """Return the template for a mediator."""
    return render_template("mediator.py.j2", subfolder="application", class_name=class_name)


def render_cqrs_handler(
    class_name: str,
    handler_type: str,
    layer_folder: str,
    folder_name: str,
    app_module: str,
    input_file: str,
    input_class: str,
    input_var: str,
    response_file: str,
    response_class: str,
    description: str,
    domain_module_base: str = "",
) -> str:
    """Return the template for a CQRS handler."""
    handler_type_lower = handler_type.lower()
    return render_template(
        "cqrs_handler.py.j2",
        subfolder="application",
        class_name=class_name,
        handler_type=handler_type,
        handler_type_lower=handler_type_lower,
        layer_folder=layer_folder,
        folder_name=folder_name,
        app_module=app_module,
        input_file=input_file,
        input_class=input_class,
        input_var=input_var,
        response_file=response_file,
        response_class=response_class,
        description=description,
        domain_module_base=domain_module_base,
    )


def render_cqrs_command(class_name: str, description: str) -> str:
    """Return the template for a CQRS command."""
    return render_template(
        "cqrs_command.py.j2",
        subfolder="application",
        class_name=class_name,
        description=description,
    )


def render_cqrs_query(dto_class_name: str, main_class_name: str, description: str) -> str:
    """Return the template for a CQRS query."""
    return render_template(
        "cqrs_query.py.j2",
        subfolder="application",
        dto_class_name=dto_class_name,
        main_class_name=main_class_name,
        description=description,
    )


def render_cqrs_response(class_name: str, description: str) -> str:
    """Return the template for a CQRS response."""
    return render_template(
        "cqrs_response.py.j2",
        subfolder="application",
        class_name=class_name,
        description=description,
    )


def render_infrastructure_repository(
    impl_class: str,
    interface_class_name: str,
    interface_file_name: str,
    entity_name: str,
    entity_file: str,
    resource_folder: str,
    domain_module_base: str = "",
) -> str:
    """Return the template for a repository implementation."""
    return render_template(
        "repository_impl.py.j2",
        subfolder="infrastructure",
        impl_class=impl_class,
        interface_class_name=interface_class_name,
        interface_file_name=interface_file_name,
        entity_name=entity_name,
        entity_file=entity_file,
        resource_folder=resource_folder,
        domain_module_base=domain_module_base,
    )


def render_infrastructure_service(
    impl_class: str,
    interface_class_name: str,
    interface_file_name: str,
    application_module_base: str = "",
) -> str:
    """Return the template for a service implementation."""
    return render_template(
        "service_impl.py.j2",
        subfolder="infrastructure",
        impl_class=impl_class,
        interface_class_name=interface_class_name,
        interface_file_name=interface_file_name,
        application_module_base=application_module_base,
    )

def render_web_package_init() -> str:
    """Return the template for web/__init__.py"""
    return render_template("__init__.py.j2", subfolder="web")


def render_vega_app(project_name: str) -> str:
    """Return the template for web/app.py"""
    return render_template("app.py.j2", subfolder="web", project_name=project_name)


def render_vega_routes_init() -> str:
    """Return the template for web/routes/__init__.py"""
    return render_template("routes_init.py.j2", subfolder="web")


def render_vega_health_route() -> str:
    """Return the template for web/routes/health.py"""
    return render_template("health_route.py.j2", subfolder="web")


def render_vega_dependencies() -> str:
    """Return the template for web/dependencies.py"""
    return render_template("dependencies.py.j2", subfolder="web")


def render_vega_main(project_name: str) -> str:
    """Return the template for presentation/web/main.py"""
    return render_template("main.py.j2", subfolder="web", project_name=project_name)


def render_standard_main(project_name: str) -> str:
    """Return the template for main.py (standard project with CLI)"""
    return render_template(
        "main_standard.py.j2", subfolder="project", project_name=project_name
    )


def render_vega_project_main(project_name: str) -> str:
    """Return the template for main.py (Vega Web project with Web and CLI)"""
    return render_template(
        "main_fastapi.py.j2", subfolder="project", project_name=project_name
    )


def render_pydantic_models_init() -> str:
    """Return the template for web/models/__init__.py"""
    return render_template("models_init.py.j2", subfolder="web")


def render_pydantic_user_models() -> str:
    """Return the template for web/models/user_models.py"""
    return render_template("user_models.py.j2", subfolder="web")


def render_vega_user_route() -> str:
    """Return the template for web/routes/users.py"""
    return render_template("users_route.py.j2", subfolder="web")


def render_shared_default_route() -> str:
    """Return the template for shared/presentation/web/routes/default.py"""
    return render_template("shared_default_route.py.j2", subfolder="web")


def render_vega_router(
    resource_name: str,
    resource_file: str,
    project_name: str,
    demo: bool = False,
) -> str:
    """Return the template for a Vega Web router.

    demo=True keeps the sample CRUD endpoints used by the legacy template,
    while the default generates an empty router skeleton.
    """
    template_name = "router.py.j2" if demo else "router_empty.py.j2"
    return render_template(
        template_name,
        subfolder="web",
        resource_name=resource_name,
        resource_file=resource_file,
        project_name=project_name,
    )


def render_vega_middleware(class_name: str, file_name: str) -> str:
    """Return the template for a Vega Web middleware"""
    return render_template(
        "middleware.py.j2",
        subfolder="web",
        class_name=class_name,
        file_name=file_name,
    )


# Backward compatibility aliases (deprecated)
render_fastapi_app = render_vega_app
render_fastapi_routes_init = render_vega_routes_init
render_fastapi_health_route = render_vega_health_route
render_fastapi_dependencies = render_vega_dependencies
render_fastapi_main = render_vega_main
render_fastapi_project_main = render_vega_project_main
render_fastapi_user_route = render_vega_user_route
render_shared_kernel_default_route = render_shared_default_route
render_fastapi_router = render_vega_router
render_fastapi_middleware = render_vega_middleware


def render_database_manager() -> str:
    """Return the template for database_manager.py"""
    return render_template("database_manager.py.j2", subfolder="sqlalchemy")


def render_alembic_ini() -> str:
    """Return the template for alembic.ini"""
    return render_template("alembic.ini.j2", subfolder="sqlalchemy")


def render_alembic_env() -> str:
    """Return the template for alembic/env.py"""
    return render_template("env.py.j2", subfolder="sqlalchemy")


def render_alembic_script_mako() -> str:
    """Return the content for alembic/script.py.mako (not a Jinja2 template)"""
    from pathlib import Path
    template_path = Path(__file__).parent / "sqlalchemy" / "script.py.mako"
    return template_path.read_text(encoding="utf-8")


def render_sqlalchemy_model(class_name: str, table_name: str) -> str:
    """Return the template for a SQLAlchemy model"""
    return render_template(
        "model.py.j2",
        subfolder="infrastructure",
        class_name=class_name,
        table_name=table_name,
    )


def render_cli_command(
    command_name: str,
    description: str,
    options: list[dict],
    arguments: list[dict],
    params_signature: str,
    params_list: list[str],
    with_interactor: bool = True,
    usage_example: str = "",
    interactor_name: str = "",
) -> str:
    """Return the template for a CLI command"""
    return render_template(
        "command.py.j2",
        subfolder="cli",
        command_name=command_name,
        description=description,
        options=options,
        arguments=arguments,
        params_signature=params_signature,
        params_list=params_list,
        with_interactor=with_interactor,
        usage_example=usage_example,
        interactor_name=interactor_name,
    )


def render_cli_command_simple(
    command_name: str,
    description: str,
    options: list[dict],
    arguments: list[dict],
    params_signature: str,
    params_list: list[str],
) -> str:
    """Return the template for a simple CLI command (non-async)"""
    return render_template(
        "command_simple.py.j2",
        subfolder="cli",
        command_name=command_name,
        description=description,
        options=options,
        arguments=arguments,
        params_signature=params_signature,
        params_list=params_list,
    )


def render_cli_commands_init() -> str:
    """Return the template for cli/commands/__init__.py with auto-discovery"""
    return render_template("commands_init.py.j2", subfolder="cli")


def render_vega_routes_init_autodiscovery() -> str:
    """Return the template for web/routes/__init__.py with auto-discovery"""
    return render_template("routes_init_autodiscovery.py.j2", subfolder="web")


# Backward compatibility alias
render_fastapi_routes_init_autodiscovery = render_vega_routes_init_autodiscovery


def render_vega_routes_init_context(context_name: str, project_name: str) -> str:
    """Return the template for web/routes/__init__.py in a bounded context"""
    return f'''"""Routes for the {context_name} bounded context.

All router modules in this package are automatically discovered
by discover_routers_ddd() in the main application.

Each route file should define a 'router' variable:
    from vega.web import Router

    router = Router()

    @router.get("/example")
    async def example():
        return {{"message": "Hello from {context_name}"}}

Routes will be automatically prefixed with /api/{context_name}/
"""
'''


def render_event(class_name: str, fields: list[dict]) -> str:
    """Return the template for a domain event"""
    return render_template(
        "event.py.j2",
        subfolder="domain",
        class_name=class_name,
        fields=fields,
    )


def render_event_handler(
    class_name: str,
    handler_func_name: str,
    event_name: str,
    event_module: str,
    decorator_args: str,
) -> str:
    """Return the template for an event handler"""
    return render_template(
        "event_handler.py.j2",
        subfolder="domain",
        class_name=class_name,
        handler_func_name=handler_func_name,
        event_name=event_name,
        event_module=event_module,
        decorator_args=decorator_args,
    )


def render_events_init() -> str:
    """Return the template for events/__init__.py with auto-discovery"""
    return render_template("events_init.py.j2", subfolder="project")


def render_listener(
    class_name: str,
    queue_name: str,
    workers: int,
    auto_ack: bool,
    visibility_timeout: int,
    retry_on_error: bool,
    max_retries: int,
    has_context: bool,
) -> str:
    """Return the template for a job listener"""
    return render_template(
        "listener.py.j2",
        subfolder="infrastructure",
        class_name=class_name,
        queue_name=queue_name,
        workers=workers,
        auto_ack=auto_ack,
        visibility_timeout=visibility_timeout,
        retry_on_error=retry_on_error,
        max_retries=max_retries,
        has_context=has_context,
    )


# DDD Pattern Renderers


def render_aggregate(class_name: str) -> str:
    """Return the template for an aggregate root."""
    from vega.cli.utils import to_snake_case
    instance_name = to_snake_case(class_name)
    return render_template(
        "aggregate.py.j2",
        subfolder="domain",
        class_name=class_name,
        instance_name=instance_name,
    )


def render_value_object(class_name: str) -> str:
    """Return the template for a value object."""
    from vega.cli.utils import to_snake_case
    instance_name = to_snake_case(class_name)
    return render_template(
        "value_object.py.j2",
        subfolder="domain",
        class_name=class_name,
        instance_name=instance_name,
    )


def render_context_init(context_name: str, project_name: str = "") -> str:
    """Return the template for bounded context __init__.py"""
    return render_template(
        "context_init.py.j2",
        subfolder="project",
        context_name=context_name,
        project_name=project_name,
    )
