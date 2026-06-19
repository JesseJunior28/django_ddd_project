from .models import Branch


class BranchRepository:
    """
    Encapsula o acesso a dados da entidade Branch.
    Equivalente ao repository que recebia o `prisma` no construtor
    no projeto TypeScript — aqui usamos o ORM do Django diretamente.
    """

    def create(self, name: str, industry_id: str) -> Branch:
        return Branch.objects.create(name=name, industry_id=industry_id)

    def find_by_id(self, id: str) -> Branch | None:
        return Branch.objects.filter(id=id).first()

    def list_all(self):
        return Branch.objects.all()

    def update(self, id: str, **fields) -> Branch | None:
        branch = self.find_by_id(id)
        if not branch:
            return None
        for key, value in fields.items():
            setattr(branch, key, value)
        branch.save()
        return branch

    def delete(self, id: str) -> bool:
        deleted, _ = Branch.objects.filter(id=id).delete()
        return deleted > 0
