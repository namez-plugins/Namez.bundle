# Namez
# Update: 8 January 2019
# Description: Launch!
# pylint: disable=undefined-variable
# pylint: disable=import-error
# Add vendor directory to module search path
import re
import datetime
import random
import urllib
import sys

import os
from dateutil.parser import parse as date_parser
from string import punctuation

# preferences
preference = Prefs
DEBUG = preference["logger.debug.enabled"]
if DEBUG:
    Log("Namez debug logging is enabled!")
else:
    Log("Namez debug logging is disabled!")


def logger(methodName, message, *args):
    if bool(DEBUG):
        stdout = methodName or ""
        stdout += " :: "
        if message:
            stdout = stdout + message
        Log(stdout, *args)


ignore_role_names = preference["ignore.role.names"].split(",")
ignore_collection_names = preference["ignore.collection.names"].split(",")
scene_title_format = preference["nameformat.scene.title"] or "{actor} - {title}"

collection_studio_format = preference["nameformat.collection.studio"]
collection_series_format = preference["nameformat.collection.series"]

match_collection_stringmap = map(
    lambda stringmap: (lambda text: text.strip(), stringmap.split('|')),
    preference["match.collection.stringmap"].split(","))

match_genre_stringmap = map(
    lambda stringmap: (lambda text: text.strip(), stringmap.split('|')),
    preference["match.genre.stringmap"].split(","))


def is_ignored_collection(name):
    for ig in ignore_collection_names:
        if ig.lower() in name.lower():
            return True
    return re.match("^[0-9pP]+$", name)


def valid_collection(name):
    return not is_ignored_collection(name)


def is_ignored_role(name):
    for ig in ignore_role_names:
        if ig.lower() in name.lower():
            return True
    return False


def safeformat(s, *args, **kwargs):
    while True:
        try:
            return clean_name(s.format(*args, **kwargs))
        except KeyError as e:
            e = e.args[0]
            kwargs[e] = "{%s}".format(e)


def clean_name(name):
    if name:
        name = re.sub(r"\s\s+", " ", name)
        name = name.strip()
        name = name.lstrip('-').strip()
    return name


def ValidatePrefs():
    pass


def Start():
    pass


def getNameFromMedia(media):
    def log(msg, *args):
        logger("getNameFromMedia", msg, *args)

    #pylint: disable=no-member
    file = None
    if media.filename and str(media.filename):
        file = os.path.basename(urllib.unquote(str(media.filename)))
    if file is None:
        try:
            log("file: %s", media.items[0].parts[0].file)
            file = os.path.basename(
                urllib.unquote(str(media.items[0].parts[0].file)))
            log("file: %s", file)
        except:
            pass
    # init name w/o file extension
    if file is not None and len(str(file)) > 0:
        log("file: %s", file)
        names = file.split(".")
        names.pop()
        name = str((".").join(names))
    else:
        name = str(media.name)
    return re.sub(r"\s\s+", " ", name)


class ParseName:
    def getBaseName(self, name):
        # replace fancy punction
        name = name.replace('–', '-').replace("_", " ")
        # de-dupe spaces
        name = re.sub(r"\s\s+", " ", name)
        return name

    def log(self, msg, *args):
        logger("ParseName", msg, *args)

    def __init__(self, name):
        self.log("init name: %s", name)
        self.name = self.getBaseName(name)
        self.raw = name
        self.publishedAt = None
        self.collections = []
        self.notes = []
        self.release = None
        self.studio = None
        self.series = None
        self.actors = set([])
        self.log("base name: %s", self.name)
        # init published at and notes
        # match (YYY-MM-DD) and facts like "(720p)"
        self.matchNotes()
        if self.notes:
            [self.addCollection(note) for note in self.notes]

        # match from settings "match.collection.stringmap"
        self.matchCollectionsFromMapping()

        # match [studio - series - episode] and "[collection]"
        self.matchGroupings()

        # actors
        self.matchActors()

        # title - scrub and build
        self.title = self.name
        self.actors = list(self.actors)
        if len(self.actors):
            for actor in self.actors:
                self.title = self.title.replace(actor, "")
        # final format
        self.title = self.title.lstrip()
        self.title = self.title.lstrip(punctuation)
        self.title = self.title.lstrip()
        self.title = self.title.lstrip(punctuation)
        self.title = clean_name(self.title.lstrip())

        self.title = safeformat(
            scene_title_format,
            title=self.title,
            actor=self.actors[0] if len(self.actors) else "",
            studio=self.studio)
        logger("Final", "title: %s", self.title)
        logger("Final", "actors %s", str(self.actors) if self.actors else None)
        logger("Final", "studio: %s", self.studio)
        logger("Final", "series: %s", self.series)
        if self.publishedAt:
            logger("Final", "publishedAt: %s", str(self.publishedAt))
        if self.release:
            logger("Final", "release: %s", self.release)
        logger("Final", "collections: %s", str(self.collections))
        logger("Final", "notes: %s", str(self.notes))

    def matchActors(self):
        self.log("matchActors name: %s", self.name)

        def parse_actors_string(name):
            and_actors = name.split(" and ")
            amp_actors = name.split(" & ")
            if self.name and len(self.name.split(" - ")) >= 2:
                if len(and_actors) >= 1:
                    [self.addActor(actor) for actor in and_actors]
                elif len(amp_actors) >= 1:
                    [self.addActor(actor) for actor in amp_actors]
                else:
                    self.addActor(actor)

        name = self.name.split(" - ")[0]
        parse_actors_string(name)
        # featured actors
        feat_actors = re.findall(r"ft\. ([aA-zZ\s&]+)", self.name)
        if len(feat_actors) > 0:
            self.log("feat_actors: %s", feat_actors)
            [parse_actors_string(actor) for actor in feat_actors]

    def matchPublishedAt(self, string):
        if not self.publishedAt:
            try:
                publishedAt = date_parser(string)
                if publishedAt:
                    self.publishedAt = publishedAt
                    self.name = clean_name(
                        self.name.replace("({})".format(string), ""))
                    self.name = clean_name(
                        self.name.replace("[{}]".format(string), ""))
                    return True
            except:
                pass
        else:
            return True

    def matchNotes(self):
        notes = re.findall(r"\(([^\)]+)\)", str(self.name))
        if notes:
            for ni, note in enumerate(notes):
                if self.matchPublishedAt(note):
                    del notes[ni]
                elif is_ignored_collection(note):
                    self.name = self.name.replace("({})".format(note), "")
                elif len(note.split(' - ')) == 2:
                    parts = note.split(' - ')
                    # assume it's (studio - series)
                    self.setStudio(parts[0])
                    self.setSeries(parts[1])
            self.notes = notes
            self.log("notes: %s", str(notes))

    def matchGroupings(self):
        groupings = list(re.findall(r"\[([^\]]+)\]", self.name))
        # clear from name
        for group in groupings:
            self.name = self.name.replace("[{}]".format(group), "").strip()
        groupings = filter(valid_collection, groupings)
        self.log("groupings: %s", groupings)
        self.log("groupings cleaned name: %s", self.name)

        if groupings:
            for group in groupings:
                # clear groupings from current name "[group]"
                self.log("group: %s", group)
                if self.matchPublishedAt(group):
                    continue
                groups = list(map(clean_name, group.split(" - ")))
                self.log("groups: %s", groups)

                if (len(groups) == 1):
                    self.addCollection(groups[0])
                elif len(groups) >= 2:
                    studio = groups[0]
                    series = groups[1]
                    if studio and not is_ignored_collection(studio):
                        self.setStudio(studio)
                    if series and not is_ignored_collection(series):
                        if series is not studio:
                            self.setSeries(series)
                    # extras
                    try:
                        release = groups[2]
                        if release and not is_ignored_collection(release):
                            self.release = release
                    except:
                        pass

                # else:
                #     default_collection = groups[0].strip()
                #     if not is_ignored_collection(default_collection):
                #         self.collections.append(default_collection)

    def matchCollectionsFromMapping(self):
        name = self.name.lower()
        if len(self.actors):
            [name.replace(actor, "") for actor in self.actors]
        name = clean_name(name)
        self.log("clean_name %s", name)
        for smap in match_collection_stringmap:
            key = smap[0]
            val = smap[1]
            if str(key) in str(self.name.lower()):
                self.addCollection(val)

    def addCollection(self, collection):
        self.collections.append(collection)

    def setStudio(self, studio):
        name = studio.replace("'", "")
        self.studio = name
        self.addCollection(name)

    def setSeries(self, series):
        name = series.replace("'", "")
        self.series = name
        self.addCollection(name)

    def addActor(self, actor):
        # pylint: disable=no-member
        self.actors.add(actor.strip())


class NZAgent(Agent.Movies):  # pylint: disable=undefined-variable
    name = "Namez"
    languages = [Locale.Language.English]
    accepts_from = ["com.plexapp.agents.localmedia"]
    primary_provider = True

    def log(self, msg, *args):
        logger("NZAgent - search", msg, *args)

    def search(self, results, media, lang):
        #pylint: disable=no-member
        name = getNameFromMedia(media)
        # self.log("media primary_metadata: %s", media.primary_metadata)
        self.log("media.id: %s", media.id)
        self.log("media name: %s", media.name)
        self.log("media year: %s", media.year)
        self.log("media.filename: %s", urllib.unquote(media.filename))
        # self.log("media primary_agent: %s", media.primary_agent)
        parsed = ParseName(name)
        self.log("parsed.name: %s", parsed.name)

        score = 75
        year = media.year
        # fname = pathlib.Path('test.py')

        if parsed.publishedAt:
            year = parsed.publishedAt.year
            self.log("parsed.publishedAt.year: %s", parsed.publishedAt.year)
            score += 30
        if parsed.collections and len(parsed.collections) > 0:
            self.log("parsed.collections: %s", str(parsed.collections))
            score += 15
        if parsed.actors and len(parsed.actors) > 0:
            self.log("parsed.actors: %s", str(parsed.actors))
            score += 35
        if parsed.studio:
            self.log("parsed.studio: %s", parsed.studio)
            score += 25
        if parsed.release:
            self.log("parsed.release: %s", parsed.release)
            score += 25
        # self.log("media publishedAt: %s", parsed.publishedAt)
        # self.log("media primary metadata: %s", str(media.primary_metadata))
        # self.log("media primary agent: %s", str(media.primary_agent))
        # self.log('media title: %s', str(media.title))
        # self.log('media show: %s', str(media.show))
        # self.log('media season: %s', str(media.season))
        # self.log('media episode: %s', str(media.episode))
        results.Append(
            MetadataSearchResult(
                id=media.id,
                name=parsed.title,
                year=year,
                lang=lang,
                score=score,
            ))

    def update(self, metadata, media, lang):
        def log(msg, *args):
            logger("update", msg, *args)

        log("metadata id: %s", str(metadata.id))
        # media
        obj = lambda: None
        obj.filename = media.items[0].parts[0].file
        log("media: %s", str(media))
        name = getNameFromMedia(obj)
        metadata.original_title = name
        log("metadata.original_title: %s", str(metadata.original_title))

        # do the things
        parsed = ParseName(name)

        # sets
        metadata.title = parsed.title
        log("metadata.title: %s", metadata.title)

        if parsed.publishedAt:
            metadata.originally_available_at = parsed.publishedAt
            logger(
                "update",
                "metadata.originally_available_at: %s",
                metadata.originally_available_at,
            )
            metadata.year = parsed.publishedAt.year
            log("metadata.year: %s", metadata.year)

        if parsed.collections and len(parsed.collections) > 0:
            log("parsed.collections: %s", str(parsed.collections))
            metadata.collections.clear()
            for c in parsed.collections:
                metadata.collections.add(c)
            log("metadata.collections: %s", str(list(metadata.collections)))

        if parsed.studio:
            metadata.studio = parsed.studio
            metadata.collections.add(
                safeformat(collection_studio_format, studio=parsed.studio))
            log("metadata.studio: %s", metadata.studio)
        if parsed.series:
            log("parsed.series: %s", parsed.series)
            metadata.collections.add(
                safeformat(collection_series_format, series=parsed.series))

        # if parsed.summary:
        #     metadata.summary = parsed.summary
        #     log("metadata.summary: %s", metadata.summary)

        if parsed.actors and len(parsed.actors) > 0:
            log("parsed.actors: %s", str(parsed.actors))
            metadata.roles.clear()
            for actor in parsed.actors:
                role = metadata.roles.new()
                role.name = actor
                # log("metadata.roles.name: %s", actor)
