# DICOM series completeness audit

Use this reference when the supplied inputs include DICOM instances. It
describes metadata relationships to check; it does not require a particular
parser. Select an available parser that exposes the needed attributes, check
its exact module/version using the host's normal discovery process, and run
all DICOM reads inside the retained batch script required by the parent skill.
Do not install or download a parser or sample data for an audit unless asked.

## Inventory and grouping

Build an inventory of relative file path, byte size, Study Instance UID,
Series Instance UID, SOP Instance UID, SOP Class UID, modality, rows, columns,
pixel spacing, instance number, and number of frames when present. Keep patient
identifiers out of the report unless required to distinguish a concrete
integrity issue. Preserve UIDs only where necessary to explain series grouping
or a duplicate.

Group instances by study and series identifiers. Do not merge two series
because their descriptions or image geometry look alike. Check for repeated
SOP Instance UIDs, missing expected instances, inconsistent dimensions or
pixel spacing within a series, and conflicting study/frame-of-reference
metadata. Treat repeated instance numbers as a flag to investigate, not
standalone proof of a missing or duplicate slice.

## Slice geometry and ordering

For images with per-instance plane geometry, compare Image Orientation
(Patient) and Image Position (Patient). The DICOM image-plane definition uses
the orientation direction cosines and position in the patient-based
coordinate system to define each image plane. When checking slice order, derive
the plane normal from the two orientation vectors and project each position
onto that normal. Compare consecutive projected positions with the expected
spacing and acquisition pattern.

Do not infer an omitted slice from Instance Number or Slice Location alone.
Account for oblique planes, localizers, repeated acquisitions, interleaved
series, variable spacing, and other multi-volume arrangements. Only call a gap
when the instances belong to one compatible acquisition and the expected
spacing/count is supported by independent evidence. Otherwise state the
observed positions and mark completeness WARNING or NOT CHECKED.

## Multi-frame objects

Do not equate one DICOM file or one SOP Instance with one image slice. Record
Number of Frames and inspect the shared and per-frame functional groups when
the object uses them. Compare per-frame positions/orientations and frame count
with the object structure and any source inventory. If a per-frame functional
groups sequence is present, its items correspond to the frames; do not count
the entire object as one plane. A plausible internal frame count still does
not prove that all expected frames or objects were delivered when no source
inventory exists.

For concatenated multi-frame objects, evaluate the concatenation as a whole
and distinguish its instances from unrelated series. Report missing or
duplicate parts only when the relevant concatenation metadata and expected
source inventory support that conclusion.

## Source completeness and reporting

Compare the received inventory with a trusted archive listing, transfer
manifest, acquisition export record, or conversion log. A manifest generated
from the received directory is not an independent expected inventory. State
which checks were possible from the supplied DICOM alone and which require the
source series or conversion record.

Report each suspected gap with its series grouping, relevant counts and
geometry, and uncertainty. Do not fabricate a slice count, silently discard
instances, rewrite metadata, or repair the source during an integrity audit.

## References

- DICOM PS3.3, [Image Plane Module](https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_c.7.6.2.html): Pixel Spacing, Image Orientation (Patient), and Image Position (Patient).
- DICOM PS3.3, [Multi-frame Functional Groups Module](https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.7.6.16.html): shared and per-frame functional groups and their relation to frame count.
