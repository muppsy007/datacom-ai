'''
This defines the corpus and related classes for our document sources
'''
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal


# Fixed download status values
class DownloadStatus(StrEnum):
    DOWNLOADED = "downloaded"
    SKIPPED = "skipped"
    FAILED = "failed"

# We should never need to mutate a source. Hence frozen here.
# 
# id is a str as it is the record -> file identifier. At this scale, it's simpler than more
# complex duplicate filename handling logic given the limited and intentional set of files
#
# min_bytes acts as idempotency check. We expect a document to be AT LEAST this size. 
@dataclass(frozen=True)
class Source:
    id: str
    url: str
    title: str
    source_type: Literal["gutenberg", "mrmuellersworld", "govinfo"]
    min_bytes: int  
    file_extension: str                        

SOURCES = [
    Source(
        id="fellowship_pdf",
        url="https://www.mrsmuellersworld.com/uploads/1/3/0/5/13054185/lord-of-the-rings-01-the-fellowship-of-the-ring_full_text.pdf",
        title="The Fellowship of the Ring",
        source_type="mrmuellersworld",
        min_bytes=500_000,
        file_extension=".pdf",
    ),
    Source(
        id="gpo_style_manual_2016",
        url="https://govinfo.gov/content/pkg/GPO-STYLEMANUAL-2016/pdf/GPO-STYLEMANUAL-2016.pdf",
        title="GPO Style Manual 2016",
        source_type="govinfo",
        min_bytes=4_000_000,
        file_extension=".pdf",
    ),
    Source(
        id="gpo_style_manual_2008",
        url="https://govinfo.gov/content/pkg/GPO-STYLEMANUAL-2008/pdf/GPO-STYLEMANUAL-2008.pdf",
        title="GPO Style Manual 2008",
        source_type="govinfo",
        min_bytes=7_000_000,
        file_extension=".pdf",
    ),
    Source(
        id="gpo_style_manual_2000",
        url="https://govinfo.gov/content/pkg/GPO-STYLEMANUAL-2000/pdf/GPO-STYLEMANUAL-2000.pdf",
        title="GPO Style Manual 2000",
        source_type="govinfo",
        min_bytes=2_000_000,
        file_extension=".pdf",
    ),
    Source(
        id="don_quixote",
        url="https://www.gutenberg.org/cache/epub/996/pg996.txt",
        title="Don Quixote",
        source_type="gutenberg",
        min_bytes=2_000_000,
        file_extension=".txt",
    ),
    Source(
        id="complete_works_shakespeare",
        url="https://www.gutenberg.org/cache/epub/100/pg100.txt",
        title="Complete Works of Shakespeare",
        source_type="gutenberg",
        min_bytes=5_000_000,
        file_extension=".txt",
    ),
    Source(
        id="war_and_peace",
        url="https://www.gutenberg.org/cache/epub/2600/pg2600.txt",
        title="War and Peace",
        source_type="gutenberg",
        min_bytes=3_000_000,
        file_extension=".txt",
    ),
    Source(
        id="moby_dick",
        url="https://www.gutenberg.org/cache/epub/2701/pg2701.txt",
        title="Moby Dick",
        source_type="gutenberg",
        min_bytes=1_200_000,
        file_extension=".txt",
    ),
    Source(
        id="middlemarch",
        url="https://www.gutenberg.org/cache/epub/145/pg145.txt",
        title="Middlemarch",
        source_type="gutenberg",
        min_bytes=1_800_000,
        file_extension=".txt",
    ),
    Source(
        id="bleak_house",
        url="https://www.gutenberg.org/cache/epub/1023/pg1023.txt",
        title="Bleak House",
        source_type="gutenberg",
        min_bytes=1_000_000,
        file_extension=".txt",
    ),
    Source(
        id="great_expectations",
        url="https://www.gutenberg.org/cache/epub/1400/pg1400.txt",
        title="Great Expectations",
        source_type="gutenberg",
        min_bytes=1_000_000,
        file_extension=".txt",
    ),
    Source(
        id="tale_of_two_cities",
        url="https://www.gutenberg.org/cache/epub/98/pg98.txt",
        title="A Tale of Two Cities",
        source_type="gutenberg",
        min_bytes=780_000,
        file_extension=".txt",
    ),
    Source(
        id="pride_and_prejudice",
        url="https://www.gutenberg.org/cache/epub/1342/pg1342.txt",
        title="Pride and Prejudice",
        source_type="gutenberg",
        min_bytes=700_000,
        file_extension=".txt",
    ),
    Source(
        id="sherlock_holmes",
        url="https://www.gutenberg.org/cache/epub/1661/pg1661.txt",
        title="The Adventures of Sherlock Holmes",
        source_type="gutenberg",
        min_bytes=580_000,
        file_extension=".txt",
    ),
    Source(
        id="les_miserables",
        url="https://www.gutenberg.org/cache/epub/135/pg135.txt",
        title="Les Misérables",
        source_type="gutenberg",
        min_bytes=3_000_000,
        file_extension=".txt",
    ),
    Source(
        id="king_james_bible",
        url="https://www.gutenberg.org/cache/epub/10/pg10.txt",
        title="The King James Bible",
        source_type="gutenberg",
        min_bytes=4_000_000,
        file_extension=".txt",
    ),
    Source(
        id="david_copperfield",
        url="https://www.gutenberg.org/cache/epub/766/pg766.txt",
        title="David Copperfield",
        source_type="gutenberg",
        min_bytes=1_800_000,
        file_extension=".txt",
    ),
    Source(
        id="brothers_karamazov",
        url="https://www.gutenberg.org/cache/epub/28054/pg28054.txt",
        title="The Brothers Karamazov",
        source_type="gutenberg",
        min_bytes=1_800_000,
        file_extension=".txt",
    ),
    Source(
        id="crime_and_punishment",
        url="https://www.gutenberg.org/cache/epub/2554/pg2554.txt",
        title="Crime and Punishment",
        source_type="gutenberg",
        min_bytes=1_100_000,
        file_extension=".txt",
    ),
  ]