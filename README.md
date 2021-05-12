# Namez Meta Agent
## Parses filenames to get metadata

Supports:

- Actors
- Studios
- Sites
- Release Dates
- Custom Collections

Sample File Names:

```
Actor - Any Title (YYYY.MM.DD) [Studio - Site - Release][other collection].mp4
Actor Name and Another Actor - Any Title (MM-DD-YYYY) [Studio - Site Name][1080p].avi
Actor Name - Any Title ft. Another Actor (DD.MM.YYYY) [Site Name][1080p][Another Collection].m4v
Actor Name - Any Title ft. Another Actor (DD.MM.YYYY) (Note1, Note2, Note3) [Site Name][1080p][Another Collection].wmv
```

### Requirements
- Python 2.7

### Installation

- Clone report into Plugins folder
- Use Plex Webtools

`./install.sh` if you need re-build python packages (dateutil)