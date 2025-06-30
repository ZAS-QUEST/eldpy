import datetime
import logging
import os
from pathlib import Path
from typing import Generator, Optional

import backoff
import pyPreservica
import requests
from lxml import etree
from unidecode import unidecode

logger = logging.getLogger()


class PreservicaAPIWrapper:
    def __init__(self) -> None:
        self.entity_client = pyPreservica.EntityAPI()
        self.content_client = pyPreservica.ContentAPI()

    def get_collections(
        self,
        parent_ref: Optional[str] = None,
        country: Optional[str] = None,
        language: Optional[str] = None,
    ) -> Generator:
        filter_values = {}

        if parent_ref:
            filter_values["xip.parent_ref"] = parent_ref

        if country:
            filter_values["imdi.country"] = country

        if language:
            filter_values["imdi.language"] = language

        for hit in self.content_client.search_index_filter_list(
            query="*",
            filter_values=filter_values,
            page_size=100,
        ):
            yield Collection(client=self, reference=hit["xip.reference"])


class PreservicaObject:
    def __init__(
        self,
        client: PreservicaAPIWrapper,
        reference: str,
        object_type: pyPreservica.EntityType,
    ) -> None:
        self.pypreservica_object = client.entity_client.entity(object_type, reference)
        self.client = client

    def __str__(self):
        return f"{self.title}[{self.reference}]"

    @property
    def reference(self) -> str:
        return self.pypreservica_object.reference

    @property
    def title(self) -> str:
        return self.pypreservica_object.title

    @property
    def description(self) -> str:
        return self.pypreservica_object.description

    @property
    def parent(self) -> str:
        return self.pypreservica_object.parent

    @property
    def security_tag(self) -> str:
        return self.pypreservica_object.security_tag


class PreservicaFolder(PreservicaObject):
    def __init__(self, client: PreservicaAPIWrapper, reference: str) -> None:
        self.pypreservica_object = client.entity_client.folder(reference)
        self.client = client
        self._identifiers: Optional[set] = None
        self._imdi_xml: Optional[str] = None
        self._last_changed_datetime: Optional[datetime.datetime] = None

    @property
    def identifiers(self) -> set:
        if self._identifiers is None:
            self._identifiers = self.client.entity_client.identifiers_for_entity(
                self.pypreservica_object
            )
        return self._identifiers

    @property
    def imdi_xml(self) -> str:
        if self._imdi_xml is None:
            self._imdi_xml = self.client.entity_client.metadata_for_entity(
                self.pypreservica_object, "http://www.mpi.nl/IMDI/Schema/IMDI"
            )
        return self._imdi_xml

    @property
    def imdi_xml_filename(self) -> str:
        title = unidecode(self.title)
        title = title.replace(" ", "_")
        title = title.replace('"', "'")
        title = title.replace("&", "_")
        title = title.replace("?", "")
        title = title.replace("!", "")
        title = title.replace("*", "")
        title = title.replace(">", "")
        title = title.replace("<", "")
        title = (title[:100] + "...") if len(title) > 100 else title
        return f"{title}[{self.reference}].xml"

    @property
    def last_changed_datetime(self) -> datetime.datetime:
        if self._last_changed_datetime is None:
            change_events = list(
                self.client.entity_client.entity_events(self.pypreservica_object)
            )
            self._last_changed_datetime = datetime.datetime.strptime(
                change_events[-1]["Date"], "%Y-%m-%dT%H:%M:%SZ"
            )
        return self._last_changed_datetime

    def save_imdi_xml_to_file(self, filepath: Path) -> bool:
        if self.imdi_xml:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(self.imdi_xml)
            return True
        logger.error(f"{self.title} [{self.reference}]: IMDI xml empty!")
        return False

    def imdi_xpath(self, xpath) -> list[etree.Element]:
        root = etree.fromstring(self.imdi_xml)
        return root.xpath(
            xpath, namespaces={"ns0": "http://www.mpi.nl/IMDI/Schema/IMDI"}
        )

    @backoff.on_exception(
        backoff.expo,
        (requests.exceptions.RequestException, pyPreservica.common.HTTPException),
        max_time=5400,
    )
    def update_imdi_xml(self, xml_string: str) -> None:
        logging.info(f"Updating IMDI xml for {self.title} [{self.reference}]")
        self.client.entity_client.update_metadata(
            self.pypreservica_object, "http://www.mpi.nl/IMDI/Schema/IMDI", xml_string
        )
        self._imdi_xml = None


class Session(PreservicaFolder):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._assets = None

    @property
    def assets(self):
        if self._assets is None:
            self._assets = []
            for x in client.entity_client.descendants(self.reference):
                if x.entity_type.name == "ASSET":
                    self._assets.append(Asset(client=client, reference=x.reference))
                else:
                    logging.error(
                        "Sessions should only contain assets. "
                        + f"Encountered {x.entity_type.name} ({x.reference})"
                    )
        return self._assets


class Asset(PreservicaObject):
    def __init__(self, client: PreservicaAPIWrapper, reference: str) -> None:
        self.pypreservica_object = client.entity_client.asset(reference)
        self.client = client
        self._file_metadata = None

    @property
    def file_metadata(self):
        if self._file_metadata is None:
            self._file_metadata = {}
            for representation in self.client.entity_client.representations(
                self.pypreservica_object
            ):
                content_objects = []
                for content_object in self.client.entity_client.content_objects(
                    representation
                ):
                    generations = []
                    for generation in self.client.entity_client.generations(
                        content_object
                    ):
                        generations.append(
                            {
                                "filename": generation.bitstreams[0].filename,
                                "effective_date": generation.effective_date,
                                "file_size": generation.bitstreams[0].length,
                                "content_url": generation.bitstreams[0].content_url,
                                "fixity": generation.bitstreams[0].fixity,
                                "format": generation.formats,
                                "properties": Asset.format_properties(
                                    generation.properties
                                ),
                                "active": generation.active,
                                "format_group": generation.format_group,
                                "original": generation.original,
                                "gen_index": generation.gen_index,
                                "bs_index": generation.bitstreams[0].bs_index,
                            }
                        )
                        if len(generation.bitstreams) > 1:
                            logging.warning(
                                f"Content object ({content_object.reference}) contains "
                                + "a generation with multiple bitstreams!"
                            )
                    content_objects.append(
                        {
                            "type": content_object.custom_type,
                            "reference": content_object.reference,
                            "title": content_object.title,
                            "security_tag": content_object.security_tag,
                            "generations": generations,
                        }
                    )
                self._file_metadata[representation.rep_type] = content_objects
        return self._file_metadata

    @staticmethod
    def format_properties(properties: list[dict]) -> dict:
        formatted_properties = {}
        for x in properties:
            formatted_properties[f'{x["PUID"]}-{x["PropertyName"]}'] = x["Value"]
        return formatted_properties


class Collection(PreservicaFolder):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def sessions(self, custom_filter_tags: Optional[set] = None) -> list:
        if custom_filter_tags:
            tags = custom_filter_tags
        else:
            tags = set(["O_OpenAccess", "U_UserAccess", "S_SubscriberAccess"])

        sessions = []
        filter_values = {
            "xip.parent_ref": self.reference,
            "xip.security_descriptor": "*",
        }
        for hit in self.client.content_client.search_index_filter_list(
            query="*", filter_values=filter_values, page_size=100
        ):
            if tags.intersection(set(hit["xip.security_descriptor"])):
                sessions.append(Session(self.client, hit["xip.reference"]))
        return sessions


if __name__ == "__main__":
    # Example usage
    from dotenv import load_dotenv

    load_dotenv()
    load_dotenv(dotenv_path=os.environ["ENV_PATH"])

    client = PreservicaAPIWrapper()

    # Retrieve collections via search
    for collection in client.get_collections(
        parent_ref=os.environ["PRESERVICA_ROOT_FOLDER_ID"]
    ):
        print(collection.reference)
        print(collection.title)
        print(collection.identifiers)
        print(len(collection.sessions()))
        print(len(collection.sessions(custom_filter_tags=set(["closed"]))))
        break

    collection = next(client.get_collections(language="Spanish"))
    print(collection.last_changed_datetime)
    print([x.text for x in collection.imdi_xpath("//ns0:Language//ns0:Name")])

    # Initiate collection via xip reference
    collection = Collection(
        client=client, reference="e0f2716f-8281-4ced-b1e8-28e68ffa5883"
    )
    print(collection.reference)
    print(collection.title)
    print(collection.identifiers)
    print(collection.imdi_xpath("//ns0:Country")[0].text)

    # Get file information of assets:
    for session in collection.sessions:
        print(session.assets)
        print(session.assets[0].file_metadata)
        break
