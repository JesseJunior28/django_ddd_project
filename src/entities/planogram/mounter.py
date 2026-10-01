"""Faithful synchronous port of the reference planogram mounter."""
from collections import defaultdict

from src.entities.branch_layout.models import BranchLayout
from src.entities.branch_layout.service import front_direction
from src.entities.planogram.models import Planogram
from src.entities.product.models import BranchProductStock


REASONS = {"inactive": "Produto inativo", "stock": "Estoque insuficiente", "dimensions": "Largura e/ou altura inválido(s)", "space": "Sem espaço para expor", "section": "Sem espaço na seção do nível"}


def side(product):
    details = product["expositionDetails"]
    return {"WIDTH": product["width"], "HEIGHT": product["height"], "LENGTH": product.get("length") or product["width"]}[details["fixedSide"]]


def product_entity(detail, branch_id=None):
    product = detail.product
    stock = BranchProductStock.objects.filter(branch_id=branch_id, sku=product.sku, ean=product.ean).first() if branch_id else None
    value = {"id": product.id, "sku": product.sku, "ean": product.ean, "name": product.name, "primaryImageUrl": product.primary_image_url,
        "isActive": product.is_active, "isRelease": product.is_release, "isNews": product.is_news, "width": product.width, "height": product.height,
        "currentStock": stock.stock if stock else 0, "expositionDetails": {"id": detail.id, "productId": product.id, "levelId": detail.level_id, "ranking": detail.ranking, "priority": detail.priority, "forefront": detail.forefront, "minStock": detail.min_stock, "fixedSide": detail.fixed_side, "isExtraExposition": detail.is_extra_exposition}}
    if product.secondary_image_url: value["secondaryImageUrl"] = product.secondary_image_url
    if product.tertiary_image_url: value["tertiaryImageUrl"] = product.tertiary_image_url
    if product.length is not None: value["length"] = product.length
    if stock and stock.original_price is not None: value["originalPrice"] = stock.original_price
    if stock and stock.discount_price is not None: value["discountPrice"] = stock.discount_price
    return value


def level_exposition(planogram, level_id, branch_id=None):
    sections, total = [], 0
    modules = list(planogram.modules.all().order_by("sequence", "id"))
    max_shelves = max((module.shelves.count() for module in modules), default=0)
    for index in range(max_shelves):
        for module in modules:
            shelves = list(module.shelves.all().order_by("sequence", "id"))
            if index >= len(shelves): continue
            shelf = shelves[index]
            for shelf_level in shelf.levels.select_related("level").filter(level_id=level_id):
                sections.append([shelf.id, shelf_level.width, []]); total += shelf_level.width
    details = list(planogram.department.levels.get(pk=level_id).expositions_details.select_related("product").order_by("ranking", "priority", "id"))
    products = [product_entity(detail, branch_id) for detail in details]
    exposed, non_exposed, remaining, counts, ranking_last = [], [], total, defaultdict(int), {}
    # A seleção respeita ranking/prioridade e consome os itens escolhidos da lista.
    rank, priority, rank_exposed = 0, 0, False
    while products:
        index = -1
        if rank_exposed:
            index = next((i for i, p in enumerate(products) if p["expositionDetails"]["ranking"] > rank), 0)
        else:
            index = next((i for i, p in enumerate(products) if p["expositionDetails"]["ranking"] == rank and p["expositionDetails"]["priority"] >= priority), -1)
            if index == -1: index = next((i for i, p in enumerate(products) if p["expositionDetails"]["ranking"] > rank), 0)
        product = products.pop(index); d = product["expositionDetails"]; rank, priority = d["ranking"], d["priority"]
        width = side(product)
        if not product["isActive"]: product["nonExpositionReason"] = REASONS["inactive"]; non_exposed.append(product); rank_exposed = False; continue
        if branch_id and (product["currentStock"] == 0 or product["currentStock"] < d["minStock"]): product["nonExpositionReason"] = REASONS["stock"]; non_exposed.append(product); rank_exposed = False; continue
        if not width: product["nonExpositionReason"] = REASONS["dimensions"]; non_exposed.append(product); rank_exposed = False; continue
        if width > remaining: product["nonExpositionReason"] = REASONS["space"]; non_exposed.append(product); rank_exposed = False; continue
        fitted = min(d["forefront"], int(remaining // (d["forefront"] * width)))
        if branch_id: fitted = min(fitted, product["currentStock"])
        last = ranking_last.get(rank, len(exposed) - 1)
        for offset in range(fitted): exposed.insert(last + 1 + offset, product)
        ranking_last[rank] = last + fitted; remaining -= width * fitted; counts[product["id"]] += fitted; rank_exposed = True
    # Repete produtos já acomodados enquanto houver largura disponível no nível.
    candidates = list(exposed)
    while remaining > 0 and candidates:
        changed = False
        for product in list(candidates):
            width = side(product)
            if width > remaining or (branch_id and counts[product["id"]] >= product["currentStock"]): candidates.remove(product); continue
            last = len(exposed) - 1 - next((i for i, x in enumerate(reversed(exposed)) if x["id"] == product["id"]), len(exposed))
            exposed.insert(last, product); counts[product["id"]] += 1; remaining -= width; changed = True
        if not changed: break
    cursor = 0
    for section in sections:
        while cursor < len(exposed) and side(exposed[cursor]) <= section[1]:
            section[2].append(exposed[cursor]); section[1] -= side(exposed[cursor]); cursor += 1
    while cursor < len(exposed):
        product = exposed.pop(cursor); product = dict(product, nonExpositionReason=REASONS["section"]); non_exposed.append(product)
    non_exposed.sort(key=lambda p: (p["expositionDetails"]["ranking"], p["expositionDetails"]["priority"]))
    return {"levelName": planogram.department.levels.get(pk=level_id).name, "exposedProducts": exposed, "nonExposedProducts": non_exposed, "totalWidth": total, "sections": {shelf_id: values for shelf_id, _, values in sections}}


def mount(planogram_id, branch_id=None, check_stock=False, layout_element_id=None):
    planogram = Planogram.objects.select_related("department__zone").prefetch_related("modules__shelves__levels__level").filter(pk=planogram_id).first()
    if not planogram: return None, "planogram"
    levels = {item.level_id for module in planogram.modules.all() for shelf in module.shelves.all() for item in shelf.levels.all()}
    expositions = {level_id: level_exposition(planogram, level_id, branch_id if check_stock else None) for level_id in levels}
    result = {"planogramId": planogram.id, "departmentName": planogram.department.name, "modules": [], "levelsProductsExpositionMap": {str(level_id): {key: value for key, value in data.items() if key != "sections"} for level_id, data in expositions.items()}}
    if planogram.name: result["name"] = planogram.name
    layout = BranchLayout.objects.prefetch_related("elements__module_configuration", "elements__rect_element").filter(branch_id=branch_id).first() if branch_id else None
    if branch_id and not layout: return None, "layout"
    mapping = {item.module_configuration.module_id: item for item in layout.elements.all() if hasattr(item, "module_configuration") and item.module_configuration.module_id} if layout else {}
    if branch_id and planogram.department.zone.is_marketing_zone and not layout_element_id: return None, "marketing"
    for module in planogram.modules.all().order_by("sequence", "id"):
        element = mapping.get(module.id)
        if branch_id and (not element or (planogram.department.zone.is_marketing_zone and element.id != layout_element_id)): continue
        orientation = element.module_configuration.orientation if element and element.module_configuration.orientation else "LEFT_TO_RIGHT"
        shelves = []
        for shelf in module.shelves.all().order_by("sequence", "id"):
            rows = []
            for item in shelf.levels.select_related("level").all().order_by("sequence", "id"):
                rows.append({"levelId": item.level_id, "name": item.level.name, "sequence": item.sequence, "hexColor": item.level.hex_color, "width": item.width, "expositionType": item.exposition_type, "exposedProducts": expositions[item.level_id]["sections"].get(shelf.id, [])})
            if orientation == "RIGHT_TO_LEFT": rows.reverse()
            shelves.append({"shelfId": shelf.id, "sequence": shelf.sequence, "levels": rows})
        result["modules"].append({"moduleId": module.id, **({"layoutElementId": element.id} if element else {}), "sequence": module.sequence, "departmentOrientation": planogram.department.orientation, "individualOrientation": orientation, "shelves": shelves})
    if branch_id and not result["modules"]: return None, "modules"
    return result, None
