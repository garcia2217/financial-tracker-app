class AppDomainError(Exception):
    """Base class for all application specific exceptions."""
    pass

class ResourceNotFoundError(AppDomainError):
    def __init__(self, resource: str, id: int | str):
        self.resource = resource
        self.id = id
        super().__init__(f"{resource} with id {id} not found")
