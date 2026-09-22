"""Sentence-level coding lexicon (Stages 0-2).

The corpus is composed of a small closed set of sentences. Every sentence is coded here by hand so that each
downstream number traces back to verbatim text. `code_records.py` fails loudly on any sentence not listed, so
nothing is silently mis-coded.

Journey stages: RECALL, EXPRESS, MATCH, RECOGNIZE, RECOVER (working model, not a proven funnel).
"""

# ---------------------------------------------------------------- openers (framing only, never behavior evidence)
OPENERS = {
    "I am having trouble finding an old picture.": "help_trouble",
    "I need help finding an old photo.": "help_request",
    "Looking for advice about finding an old photo.": "help_advice",
    "The search is frustrating.": "affect_frustration",
    "Searching for a specific memory takes too much work.": "effort_claim",
    "Google Photos, please make this easier.": "request_to_vendor",
    "Does anyone else have this problem?": "community_solicit",
}

# ---------------------------------------------------------------- retrieval object -> class
OBJECTS = {
    "the restaurant near Tokyo station.": "travel_place",
    "the hotel we stayed at during a trip.": "travel_place",
    "that small cafe from our Goa trip.": "travel_place",
    "the waterfall from our road trip.": "travel_place",
    "our Kerala houseboat photos.": "travel_place",
    "the birthday dinner.": "event_social",
    "the concert selfie.": "event_social",
    "the picture from the day we moved house.": "event_social",
    "the picture from our office party.": "event_social",
    "the sangeet.": "event_social",
    "the old family group photo.": "family_person",
    "a picture with my college friends.": "family_person",
    "my cousin at the concert.": "family_person",
    "our Diwali family photo.": "family_person",
    "a photo of my grandfather at the wedding.": "family_person",
    "my daughter wearing the red dress.": "family_person",
    "a photo of my grandparents' wedding album.": "family_person",
    "the insurance document.": "document_screenshot",
    "the boarding pass screenshot.": "document_screenshot",
    "the landlord WhatsApp screenshot.": "document_screenshot",
    "the recipe screenshot.": "document_screenshot",
    "a screenshot of a product I wanted.": "document_screenshot",
    "the old meme I saved.": "document_screenshot",
    "the photo of a prescription.": "medical",
    "the medicine box I photographed.": "medical",
    "the picture I sent to my doctor.": "medical",
    "the photo from when I was sick.": "medical",
    "the lamp I wanted to buy.": "physical_object",
    "a yellow truck.": "unspecified_object",
    "the parking sign I photographed.": "physical_object",
}

# The brief says "do not force a category when evidence is insufficient". These objects are judgement calls: the text
# does not settle the class. value = (alternative class, why it is uncertain). Objects not listed name their kind
# explicitly (e.g. "screenshot", "document", "prescription", "trip", "wedding") and count as clear.
OBJECT_JUDGEMENT = {
    "the old meme I saved.": ("event_social", "a saved image; may not be a screenshot or document"),
    "our Diwali family photo.": ("event_social", "both a family photo and a festival occasion"),
    "my cousin at the concert.": ("event_social", "both a person and an event"),
    "a photo of my grandparents' wedding album.": ("event_social", "a family item and a wedding occasion; unclear whether it is a photographed print"),
    "a photo of my grandfather at the wedding.": ("event_social", "both a person and an event"),
    "the photo from when I was sick.": ("event_social", "a personal episode; medical only by inference"),
    "the picture I sent to my doctor.": ("document_screenshot", "a medical exchange; content of the picture not stated"),
    "the medicine box I photographed.": ("physical_object", "a physical object that is also medical"),
    "a screenshot of a product I wanted.": ("physical_object", "a screenshot of a product; class depends on whether product or screenshot matters"),
    "the lamp I wanted to buy.": ("document_screenshot", "a product; may be a screenshot rather than a photo of the lamp"),
    "a yellow truck.": ("physical_object", "described by appearance only; kind of object (toy, vehicle, photo subject) is not stated"),
}
OBJECT_CLASS_LABEL = {
    "travel_place": "Trip / place memory",
    "event_social": "Event / social occasion",
    "family_person": "Family / person memory",
    "document_screenshot": "Document / screenshot / saved image",
    "medical": "Medical-related image",
    "physical_object": "Physical object / product",
    "unspecified_object": "Unspecified (described by appearance only)",
}

# ---------------------------------------------------------------- memory slot
# remembered: what the user says they retain; forgotten: what they explicitly lack ([] if the sentence names none)
# express_barrier: sentence explicitly says the memory is hard to turn into a query / narrowing action
MEMORY = {
    "I remember the story around the photo more clearly than its metadata.":
        dict(code="M01_story_over_metadata", remembered=["story"], forgotten=[], express_barrier=False),
    "I remember what the object looked like, but not what it was called.":
        dict(code="M02_object_look_not_name", remembered=["visual_appearance", "object"], forgotten=["object_name"], express_barrier=True),
    "I remember the people and situation but not the date.":
        dict(code="M03_people_situation_not_date", remembered=["people", "situation"], forgotten=["date"], express_barrier=False),
    "I remember the place generally, but not its name.":
        dict(code="M04_place_general_not_name", remembered=["place"], forgotten=["place_name"], express_barrier=False),
    "I can recognize it if I see it, but I don't know how to narrow the results.":
        dict(code="M05_recognize_cannot_narrow", remembered=["recognition_ability"], forgotten=[], express_barrier=True),
    "I remember the color, setting, or people but not a useful keyword.":
        dict(code="M06_color_setting_people_no_keyword", remembered=["color", "setting", "people"], forgotten=["searchable_keyword"], express_barrier=True),
    "I remember roughly when it happened, but not the exact day.":
        dict(code="M07_approx_time_not_day", remembered=["approximate_time"], forgotten=["exact_day"], express_barrier=False),
    "I remember who was there and what we were doing, but not the album.":
        dict(code="M08_people_activity_not_album", remembered=["people", "activity"], forgotten=["album"], express_barrier=False),
    "I remember the photo exists, but not how I originally found it.":
        dict(code="M09_exists_not_original_path", remembered=["existence"], forgotten=["original_retrieval_path"], express_barrier=False),
    "I know approximately which year it was, but not the month.":
        dict(code="M10_year_not_month", remembered=["approximate_time"], forgotten=["month"], express_barrier=False),
    "I remember a visual detail that is hard to describe in a search box.":
        dict(code="M11_visual_detail_hard_to_describe", remembered=["visual_appearance"], forgotten=[], express_barrier=True),
    "I remember what was happening but not the exact words.":
        dict(code="M12_activity_not_exact_words", remembered=["activity"], forgotten=["exact_wording"], express_barrier=True),
}

# ---------------------------------------------------------------- behavior / outcome slot (exactly one per record)
# state: mutually exclusive retrieval state stated in the record
#   exit_path | recovery_dependent | candidate_inspection | first_attempt
# outcome: spec categories; None -> Unknown.  signals: severity signals named in the spec.
BEHAVIOR = {
    "I searched by person and place together.":
        dict(code="B01_person_place_search", state="first_attempt", stages=["EXPRESS"], outcome=None, signals=[]),
    "I searched for text that might be in the image.":
        dict(code="B02_text_in_image_search", state="first_attempt", stages=["EXPRESS"], outcome=None, signals=[]),
    "I searched by date and got too many results.":
        dict(code="B03_date_search_too_many", state="candidate_inspection", stages=["EXPRESS", "MATCH"], outcome=None, signals=["large_candidate_set"]),
    "I opened likely results one by one.":
        dict(code="B04_open_results_one_by_one", state="candidate_inspection", stages=["RECOGNIZE"], outcome=None, signals=["candidate_inspection"]),
    "I tried different wording.":
        dict(code="B05_different_wording", state="recovery_dependent", stages=["EXPRESS", "RECOVER"], outcome=None, signals=["reformulation"]),
    "I tried an object keyword.":
        dict(code="B06_object_keyword", state="first_attempt", stages=["EXPRESS"], outcome=None, signals=[]),
    "I switched between search terms and albums.":
        dict(code="B07_switch_terms_albums", state="recovery_dependent", stages=["RECOVER"], outcome=None, signals=["strategy_switch"]),
    "I switched to another device or photo app.":
        dict(code="B08_other_device_or_app", state="exit_path", stages=["RECOVER"], outcome="external_workaround", signals=["strategy_switch", "external_workaround"]),
    "I searched a person's name and then browsed.":
        dict(code="B09_person_then_browse", state="recovery_dependent", stages=["EXPRESS", "RECOVER"], outcome=None, signals=["strategy_switch", "browsing"]),
    "I gave up and asked someone else to send the photo.":
        dict(code="B10_gave_up_asked_someone", state="exit_path", stages=["RECOVER"], outcome="abandoned", signals=["abandonment", "external_workaround"]),
    "I looked through the timeline manually.":
        dict(code="B11_timeline_manual", state="candidate_inspection", stages=["RECOVER", "RECOGNIZE"], outcome=None, signals=["browsing"]),
    "I could not find it.":
        dict(code="B12_could_not_find", state="exit_path", stages=["RECOVER"], outcome="failed", signals=["failure"]),
    "I looked through a very large set of thumbnails.":
        dict(code="B13_large_thumbnail_set", state="candidate_inspection", stages=["RECOGNIZE"], outcome=None, signals=["browsing", "large_candidate_set"]),
    "I found a similar photo but not the exact one.":
        dict(code="B14_similar_not_exact", state="candidate_inspection", stages=["RECOGNIZE"], outcome="similar_uncertain", signals=["uncertainty"]),
    "I found it after several attempts.":
        dict(code="B15_found_after_several_attempts", state="recovery_dependent", stages=["RECOVER"], outcome="found_with_effort", signals=["repeated_attempts"]),
    "I used a date range and manually compared candidates.":
        dict(code="B16_date_range_compare", state="candidate_inspection", stages=["EXPRESS", "RECOGNIZE"], outcome=None, signals=["candidate_inspection"]),
    "I tried several related words.":
        dict(code="B17_several_related_words", state="recovery_dependent", stages=["EXPRESS", "RECOVER"], outcome=None, signals=["reformulation", "repeated_attempts"]),
    "I searched a few keywords and then scrolled.":
        dict(code="B18_keywords_then_scroll", state="recovery_dependent", stages=["EXPRESS", "RECOVER"], outcome=None, signals=["strategy_switch", "browsing"]),
}

# ---------------------------------------------------------------- closing sentences (optional 5th slot)
CLOSERS = {
    "I can recognize the image if I see it, but getting to it is the hard part.":
        dict(code="C01_recognize_but_access_hard", stages=["RECOGNIZE"], signals=[], flag="recognition_retained"),
    "There are thousands of images in the account.":
        dict(code="C02_thousands_of_images", stages=[], signals=[], flag="large_library"),
    "I have been using Photos for years.":
        dict(code="C03_years_of_use", stages=[], signals=[], flag="long_tenure"),
    "It feels much easier when I know an exact date or person's name.":
        dict(code="C04_easier_with_precise_identifier", stages=["EXPRESS"], signals=[], flag="precise_identifier_contrast"),
    "I usually remember the story around the picture better than its metadata.":
        dict(code="C05_story_over_metadata", stages=["RECALL"], signals=[], flag="story_memory"),
    "I know the photo exists because I have seen it before.":
        dict(code="C06_knows_photo_exists", stages=["RECALL"], signals=[], flag="existence_certain"),
    "The problem is not taking the photo; it is finding it later.":
        dict(code="C07_finding_not_taking", stages=[], signals=[], flag="framing"),
    "Sometimes I get a lot of plausible results and still cannot tell which one is right.":
        dict(code="C08_plausible_cannot_tell", stages=["MATCH", "RECOGNIZE"], signals=["uncertainty", "large_candidate_set"], flag="cannot_confirm_candidate"),
}

# ---------------------------------------------------------------- off-topic (SIM-N*) records
OFFTOPIC = {
    "I accidentally deleted a photo and need to restore it.": "deleted_photo_restore",
    "I need help with partner sharing.": "sharing",
    "The app is using too much battery.": "battery",
    "How do I change notification settings?": "settings",
    "The new editing interface is confusing.": "editing_ui",
    "My photos are taking too much storage.": "storage",
    "How do I change the app theme?": "settings",
    "Backup is taking forever on my phone.": "backup",
    "I want to print a photo book.": "printing",
    "Face grouping stopped working after an update.": "face_grouping_defect",
    "The video editor crashes when I export.": "editing_defect",
    "How do I free up storage without deleting my photos?": "storage",
    "How can I create a collage?": "collage",
    "I want to share an album with my family.": "sharing",
    "The app keeps asking me to upgrade storage.": "storage",
}
# Deleted-photo restore is the only off-topic topic with retrieval-like intent (get a photo back), but it carries no
# memory or behavior evidence and is a restore flow rather than search -> "possibly relevant", excluded from denominators.
POSSIBLY_RELEVANT_TOPICS = {"deleted_photo_restore"}
