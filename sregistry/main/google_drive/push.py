'''

Copyright (C) 2017 The Board of Trustees of the Leland Stanford Junior
University.
Copyright (C) 2017 Vanessa Sochat.

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or (at your
option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public
License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

'''

from sregistry.client import Singularity
from sregistry.logger import bot, ProgressBar
from sregistry.utils import (
    get_image_hash,
    get_thumbnail,
    parse_image_name
)

from sregistry.main.google_storage.utils import prepare_metadata
from googleapiclient.http import MediaFileUpload
from retrying import retry
import requests
import base64
import json
import sys
import os



def push(self, path, name, tag=None):
    '''push an image to Google Cloud Drive, meaning uploading it
    
    path: should correspond to an absolte image path (or derive it)
    name: should be the complete uri that the user has requested to push.
    tag: should correspond with an image tag. This is provided to mirror Docker
    '''
    # The root of the drive for containers (the parent folder)
    parent = self._get_or_create_folder(self._base)

    image = None
    path = os.path.abspath(path)
    bot.debug("PUSH %s" % path)

    if not os.path.exists(path):
        bot.error('%s does not exist.' %path)
        sys.exit(1)

    names = parse_image_name(name,tag=tag)
    if names['version'] is None:
        version = get_image_hash(path)
        names = parse_image_name(name, tag=tag, version=version)

    # get container metadata
    cli = Singularity()
    metadata = cli.inspect(image_path=path, quiet=True)
    metadata = json.loads(metadata)

    # Update metadata with names, flatten to only include labels
    metadata = metadata['data']
    metadata.update(names)
    metadata.update(metadata['attributes']['labels'])
    del metadata['attributes']

    file_metadata = {
        'name': names['storage'],
        'mimeType' : 'application/octet-stream',
        'parents': [parent['id']],
        'properties': metadata
    }

    media = MediaFileUpload(path,resumable=True)
    try:
        bot.spinner.start()
        image = self._service.files().create(body=file_metadata,
                                             media_body=media,
                                             fields='id').execute()

        # Add a thumbnail!
        thumbnail = get_thumbnail()

        with open(thumbnail, "rb") as f:
            body = { "contentHints": { 
                     "thumbnail": { "image": base64.urlsafe_b64encode(f.read()).decode('utf8'),
                                     "mimeType": "image/png" }
                                  }}
            image = self._service.files().update(fileId=image['id'],
                                                 body = body).execute()
 
        bot.spinner.stop()

    except HttpError:
        bot.error('Error uploading %s' %path)
        pass

    return image
