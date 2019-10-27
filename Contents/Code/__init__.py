# AdultDVDEmpire
# Update: 8 January 2019
# Description: New updates from a lot of diffrent forks and people. Please read README.md for more details.

# Add vendor directory to module search path
import re
import datetime
import random
import urllib
import sys

import os
import dateparser

# preferences
preference = Prefs
DEBUG = preference["logger.debug.enabled"]
if DEBUG:
    Log("Namez debug logging is enabled!")
else:
    Log("Namez debug logging is disabled!")

ignore_role_names = preference["ignore.role.names"].split(",")
ignore_collection_names = preference["ignore.collection.names"].split(",")


def is_ignored_collection(name):
    for ig in ignore_collection_names:
        if ig.lower() in name.lower():
            return True
    return re.match("^[0-9pP]+$", name)
    # return False


def is_ignored_role(name):
    for ig in ignore_role_names:
        if ig.lower() in name.lower():
            return True
    return False


scene_title_format = preference["nameformat.scene.title"]
collection_studio_format = preference["nameformat.collection.studio"]
collection_series_format = preference["nameformat.collection.series"]


def ValidatePrefs():
    pass


def logger(methodName, message, *args):
    if bool(DEBUG):
        Log(methodName + " :: " + message, *args)


def Start():
    pass


def getNameFromMedia(media):
    file = None
    if media.filename and str(media.filename):
        file = os.path.basename(urllib.unquote(str(media.filename)))
    if file is None:
        try:
            logger("getNameFromMedia" "file: %s", media.items[0].parts[0].file)
            file = os.path.basename(urllib.unquote(str(media.items[0].parts[0].file)))
            logger("getNameFromMedia", "file: %s", file)
        except:
            pass
    # init name w/o file extension
    if file is not None and len(str(file)) > 0:
        logger("ParseName", "file: %s", file)
        names = file.split(".")
        names.pop()
        name = str((".").join(names))
    else:
        name = str(media.name)
    return re.sub("\s\s+", " ", name)


class ParseName:
    def __init__(self, name):
        logger("ParseName", "init name: %s", name)
        self.name = name
        self.raw = name
        self.publishedAt = None
        self.collections = []
        self.release = None
        self.studio = None
        self.series = None
        self.actors = None
        self.notes = []

        logger("ParseName", "name: %s", self.name)
        # init published at

        notes = re.findall("\(([^\)]+)\)", str(self.name))
        if notes:
            logger("ParseName", "notes: %s", str(notes))
            for ni, note in enumerate(notes):
                publishedAt = dateparser.parse(note)
                if publishedAt:
                    self.publishedAt = publishedAt
                    self.name = self.name.replace("(%s)" % note, "")
                    del notes[ni]
            self.notes = notes

        # try:
        groupings = re.findall("\[([^\]]+)\]", self.name)
        logger("ParseName", "groupings: %s", groupings)

        if "pov" in self.name.lower():
            self.collections.append("POV")

        if groupings:
            for gi, group in enumerate(groupings):
                self.name = self.name.replace("[%s]" % group, "")
                # check if has release code
                groups = map(lambda name: name.strip(), group.split(" - "))
                # logger("ParseName", "groups[%s]: %s", gi, groups)
                if len(groups) == 3:
                    studio = groups[0].strip()
                    series = groups[1].strip()
                    release = groups[2].strip()
                    if studio and not is_ignored_collection(studio):
                        self.studio = studio.replace("'", "")
                    if series and not is_ignored_collection(series):
                        if series is not studio:
                            self.series = series.replace("'", "")
                    if release and not is_ignored_collection(release):
                        self.release = release

                elif len(groups) == 2:
                    studio = groups[0].strip()
                    series = groups[1].strip()
                    if studio and not is_ignored_collection(studio):
                        self.studio = studio.replace("'", "")
                    if series and not is_ignored_collection(series):
                        if series.lower() is not studio.lower():
                            self.series = series.replace("'", "")
                else:
                    if not is_ignored_collection(groups[0]):
                        self.collections.append(groups[0].replace("'", ""))

        self.name = re.sub("\s\s+", " ", self.name)
        self.name = self.name.replace("_", " ")

        # actors
        if self.name and len(self.name.split(" - ")) >= 2:
            name = self.name.split(" - ")[0]
            if name.split(" and ") and len(name.split(" and ")) > 1:
                self.actors = name.split(" and ")
            elif name.split(" & ") and len(name.split(" & ")) > 1:
                self.actors = name.split(" & ")
            else:
                self.actors = [name]

        # featured actors
        featured = re.findall("ft\. ([aA-zZ\s&]+)", self.name)
        if featured and len(featured) > 0:
            logger("ParseName", "featured: %s", featured)
            for fi, feat in enumerate(featured):
                names_ampersand = feat.strip().split(" & ")
                names_and = feat.strip().split(" and ")
                if names_ampersand and len(names_ampersand) > 1:
                    if self.actors is None:
                        self.actors = []
                    for n in names_ampersand:
                        self.actors.append(n)
                elif names_and and len(names_and) > 1:
                    if self.actors is None:
                        self.actors = []
                    for n in names_and:
                        self.actors.append(n)
                else:
                    if self.actors is None:
                        self.actors = []
                    self.actors.append(feat.strip())


class NZAgent(Agent.Movies):  # pylint: disable=undefined-variable
    name = "Namez"
    languages = [Locale.Language.English]
    accepts_from = ["com.plexapp.agents.localmedia"]
    primary_provider = True

    def search(self, results, media, lang):
        name = getNameFromMedia(media)
        # logger("search", "media primary_metadata: %s", media.primary_metadata)
        logger("search", "media.id: %s", media.id)
        # logger("search", "media primary_agent: %s", media.primary_agent)
        # logger("search", "media filename: %s", media.filename)
        # logger("search", "media name: %s", media.name)
        # logger("search", "media year: %s", media.year)
        # logger("search", "media show: %s", media.show)
        parsed = ParseName(name)
        logger("search", "parsed.name: %s", parsed.name)

        score = 75
        year = media.year

        if parsed.publishedAt:
            year = parsed.publishedAt.year
            logger("search", "parsed.publishedAt.year: %s", parsed.publishedAt.year)
            score += 15
        if parsed.collections and len(parsed.collections) > 0:
            logger("search", "parsed.collections: %s", str(parsed.collections))
            score += 20
        if parsed.actors and len(parsed.actors) > 0:
            logger("search", "parsed.actors: %s", str(parsed.actors))
            score += 30
        if parsed.studio:
            logger("search", "parsed.studio: %s", parsed.studio)
            score += 25
        elif parsed.collections:
            logger("search", "parsed.collection: %s", parsed.collections)
            score += 25
        elif parsed.release:
            logger("search", "parsed.release: %s", parsed.release)
            score += 25
        # logger("search", "media publishedAt: %s", parsed.publishedAt)

        # logger("search", "media primary metadata: %s", str(media.primary_metadata))
        # logger("search", "media primary agent: %s", str(media.primary_agent))
        # logger('search', 'media title: %s', str(media.title))
        # logger('search', 'media show: %s', str(media.show))

        # logger('search', 'media season: %s', str(media.season))
        # logger('search', 'media episode: %s', str(media.episode))
        results.Append(
            MetadataSearchResult(
                id=media.id,
                name=scene_title_format.format(title=parsed.name),
                year=year,
                lang=lang,
                score=score,
            )
        )

    def update(self, metadata, media, lang):
        logger("update", "metadata id: %s", str(metadata.id))
        # media
        obj = lambda: None
        obj.filename = media.items[0].parts[0].file
        name = getNameFromMedia(obj)
        metadata.original_title = name
        logger("update", "metadata.original_title: %s", str(metadata.original_title))
        parsed = ParseName(name)

        # sets
        metadata.title = scene_title_format.format(title=parsed.name)
        logger("update", "metadata.title: %s", metadata.title)

        if parsed.publishedAt:
            metadata.originally_available_at = parsed.publishedAt
            logger(
                "update",
                "metadata.originally_available_at: %s",
                metadata.originally_available_at,
            )
            metadata.year = parsed.publishedAt.year
            logger("update", "metadata.year: %s", metadata.year)

        if (
            (parsed.collections and len(parsed.collections) > 0)
            or parsed.studio
            or parsed.series
        ):
            metadata.collections.clear()
        if parsed.collections and len(parsed.collections) > 0:
            logger("update", "parsed.collections: %s", str(parsed.collections))
            for c in parsed.collections:
                metadata.collections.add(c)
            # logger("update", "metadata.collections: %s", str(metadata.collections))

        if parsed.studio:
            metadata.studio = parsed.studio
            logger("update", "metadata.studio: %s", metadata.studio)
        if parsed.series:
            logger("update", "parsed.series: %s", parsed.series)
            metadata.collections.add(
                collection_series_format.format(
                    studio=parsed.studio, series=parsed.series
                )
            )

        # if parsed.summary:
        #     metadata.summary = parsed.summary
        #     logger("update", "metadata.summary: %s", metadata.summary)

        if parsed.actors and len(parsed.actors) > 0:
            logger("update", "parsed.actors: %s", str(parsed.actors))
            metadata.roles.clear()
            for actor in parsed.actors:
                role = metadata.roles.new()
                role.name = actor
                # logger("update", "metadata.roles.name: %s", actor)
