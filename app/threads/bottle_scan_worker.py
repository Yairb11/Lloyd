import re
from pathlib import Path
from typing import Dict, List, Optional, Set
import cv2
import easyocr
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal
from thefuzz import fuzz
from ultralytics import YOLO

from app.threads.cancellable_worker import CancellableWorker

GLOBAL_BAR_BRANDS: Dict[str, List[str]] = {
    "Lagavulin": ["lagavulin", "lagavuli"],
    "Aberlour": ["aberlour", "abunadh", "a'bunadh"],
    "The Balvenie": ["balvenie", "doublewood", "caribbean cask"],
    "Glen Garioch": ["glen garioch", "garioch", "founder's reserve", "founders reserve"],
    "Ballantine's": ["ballantine", "ballantines", "ballantine's"],
    "Monkey Shoulder": ["monkey shoulder", "batch 27"],
    "Glenfiddich": ["glenfiddich"],
    "The Glenlivet": ["glenlivet"],
    "The Macallan": ["macallan"],
    "Laphroaig": ["laphroaig"],
    "Ardbeg": ["ardbeg"],
    "Talisker": ["talisker"],
    "Highland Park": ["highland park"],
    "Johnnie Walker": ["johnnie walker", "black label", "red label"],
    "Chivas Regal": ["chivas regal", "chivas"],
    "Maker's Mark": ["maker's mark", "makers mark", "mark 101"],
    "Buffalo Trace": ["buffalo trace"],
    "Woodford Reserve": ["woodford reserve"],
    "Jack Daniel's": ["jack daniel", "jack daniels", "old no 7"],
    "Jim Beam": ["jim beam"],
    "Bulleit": ["bulleit"],
    "Jameson": ["jameson"],
    "Hennessy": ["hennessy", "henn", "jas hennessy", "vsop"],
    "Rémy Martin": ["remy martin"],
    "Courvoisier": ["courvoisier"],
    "The Kraken": ["kraken", "black spiced"],
    "Bacardi": ["bacardi"],
    "Captain Morgan": ["captain morgan"],
    "Havana Club": ["havana club"],
    "Diplomático": ["diplomatico"],
    "Gordon's Pink Gin": ["premium pink", "pink gin", "gordon's pink"],
    "Gordon's Gin": ["gordon", "gordons", "gordon's"],
    "Roku Gin": ["roku", "japanese craft gin"],
    "Tanqueray": ["tanqueray"],
    "Bombay Sapphire": ["bombay sapphire", "bombay"],
    "Hendrick's Gin": ["hendrick", "hendricks"],
    "Beefeater": ["beefeater"],
    "Absolut Vodka": ["absolut"],
    "Grey Goose": ["grey goose"],
    "Smirnoff": ["smirnoff"],
    "Ketel One": ["ketel one"],
    "Belvedere": ["belvedere"],
    "Tito's": ["titos", "tito's handmade"],
    "Aperol": ["aperol", "aperitivo 1919"],
    "Martini & Rossi Vermouth": ["martini", "extra dry", "rosso", "bianco"],
    "Campari": ["campari"],
    "Cointreau": ["cointreau"],
    "Baileys": ["baileys"],
    "Kahlúa": ["kahlua"],
    "Jägermeister": ["jagermeister"],
    "Isola Wine": ["isola"],
}

SPIRIT_TYPES = [
    "bourbon", "scotch", "single malt", "whisky", "whiskey", 
    "vermouth", "gin", "vodka", "rum", "tequila", "mezcal", "cognac", "liqueur"
]

OCR_STOPWORDS: Set[str] = {
    "distillery", "distilled", "matured", "cask", "oak", "wood", "years", 
    "aged", "batch", "bottle", "vol", "alc", "proof", "whisky", "whiskey",
    "scotch", "malt", "estd", "since", "product", "scotland", "kentucky",
    "imported", "finest", "original", "blend", "blended"
}

class BottleScanWorker(CancellableWorker):
    scan_finished = pyqtSignal(list)
    scan_failed = pyqtSignal(str)

    def __init__(self, image_input: str | Path | np.ndarray, yolo_model: str = "yolo11n.pt", gpu: bool = False):
        super().__init__()
        self.image_input = image_input
        self.yolo_model = yolo_model
        self.gpu = gpu

    def _preprocess_crop(self, crop: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8))
        return clahe.apply(gray)

    def _clean_text(self, tokens: List[str]) -> str:
        text = " ".join(tokens).lower()
        return re.sub(r"[^a-z0-9\s']", " ", text)

    def _resolve_identity(self, ocr_tokens: List[str]) -> Optional[str]:
        cleaned_text = self._clean_text(ocr_tokens)
        if not cleaned_text.strip():
            return None

        best_brand, highest_score = None, 0
        for brand_name, triggers in GLOBAL_BAR_BRANDS.items():
            for trigger in triggers:
                if len(trigger) <= 4:
                    if re.search(r'\b' + re.escape(trigger) + r'\b', cleaned_text):
                        score = 95
                    else:
                        score = 0
                else:
                    if trigger in cleaned_text:
                        score = 95
                    else:
                        score = fuzz.token_set_ratio(trigger, cleaned_text)

                if score > highest_score and score >= 75:
                    highest_score = score
                    best_brand = brand_name

        if best_brand:
            return best_brand

        for stype in SPIRIT_TYPES:
            if re.search(r'\b' + re.escape(stype) + r'\b', cleaned_text):
                return stype.title()

        words = [w for w in cleaned_text.split() if w not in OCR_STOPWORDS and len(w) >= 5]
        if words:
            return f"{words[0].capitalize()} Bottle"

        return None

    def _nms_boxes(self, boxes: List[List[int]], iou_threshold: float = 0.35) -> List[List[int]]:
        if not boxes:
            return []
        boxes = sorted(boxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]), reverse=True)
        selected = []
        for b in boxes:
            keep = True
            for s in selected:
                x1 = max(b[0], s[0])
                y1 = max(b[1], s[1])
                x2 = min(b[2], s[2])
                y2 = min(b[3], s[3])
                inter = max(0, x2 - x1) * max(0, y2 - y1)
                area_b = (b[2] - b[0]) * (b[3] - b[1])
                area_s = (s[2] - s[0]) * (s[3] - s[1])
                iou = inter / float(area_b + area_s - inter)
                if iou > iou_threshold or (inter / float(area_b)) > 0.70:
                    keep = False
                    break
            if keep:
                selected.append(b)
        return selected

    def do_work(self):
        try:
            if isinstance(self.image_input, (str, Path)):
                path = Path(self.image_input)
                if not path.is_file():
                    self.scan_failed.emit(f"File not found: {path.resolve()}")
                    return
                image = cv2.imread(str(path))
                if image is None:
                    self.scan_failed.emit(f"Failed to decode image: {path.resolve()}")
                    return
            elif isinstance(self.image_input, np.ndarray):
                image = self.image_input
            else:
                self.scan_failed.emit("Invalid input type. Expected Path or np.ndarray.")
                return

            h, w, _ = image.shape
            yolo = YOLO(self.yolo_model)
            ocr = easyocr.Reader(["en"], gpu=self.gpu)

            results = yolo.predict(
                source=image,
                conf=0.18,
                iou=0.40,
                verbose=False
            )

            detected_boxes = []
            for result in results:
                for box in result.boxes.xyxy.cpu().numpy():
                    x1, y1, x2, y2 = [int(v) for v in box]
                    bw, bh = x2 - x1, y2 - y1
                    if bh > (bw * 1.1) and bh > (h * 0.12) and bw > 30:
                        detected_boxes.append([max(0, x1), max(0, y1), min(w, x2), min(h, y2)])

            clean_boxes = self._nms_boxes(detected_boxes, iou_threshold=0.35)
            shelf_height = max(1, h // 3)
            clean_boxes.sort(key=lambda b: ((b[1] + b[3]) // (2 * shelf_height), b[0]))

            bottles_found: List[str] = []

            for idx, (x1, y1, x2, y2) in enumerate(clean_boxes, 1):
                if self.is_cancelled():
                    return
                crop = image[y1:y2, x1:x2]
                processed = self._preprocess_crop(crop)
                tokens = ocr.readtext(processed, detail=0)
                name = self._resolve_identity(tokens)

                if name and (not bottles_found or bottles_found[-1] != name):
                    bottles_found.append(name)
            self.scan_finished.emit(bottles_found)

        except Exception as e:
            self.scan_failed.emit(str(e))