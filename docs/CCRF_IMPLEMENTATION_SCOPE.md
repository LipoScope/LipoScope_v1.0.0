# CCRF Version 1 implementation scope

LipoScope uses the four official Lipedema Foundation CCRF Version 1 classification-specific REDCap data dictionaries as its field-definition source.

## Source elements retained

For each source row, the generated schema retains the variable name, form, section heading, field type, field label, coded choices or calculation cell, field note, validation type, minimum and maximum, identifier flag, branching logic, required-field flag, alignment, survey question number, matrix metadata, annotation and source-row reference.

## Conditional questions

Conditional questions are not treated as privacy-restricted fields. LipoScope evaluates the official branching expression associated with the field and shows the question when the expression is true. A hidden field is excluded from completion while it is not applicable.

If a response was entered before the branch became inactive, the value is retained and labelled `inactive_with_value`. LipoScope does not silently delete it. The value is identified in the record summary and data-quality export, and the user may clear it.

## Direct identifiers and files

Fields marked as identifiers in the official dictionary remain visible in the data dictionary but are not stored in browser-local records or populated in exports. File controls may record a selected filename during the active browser session, but file contents and signatures are not retained in saved records.

## Calculated fields

LipoScope executes no inferred formula. A formula may be implemented only when an exact expression is supplied by the official CCRF source and its REDCap behaviour is validated.

The current official classification-specific dictionaries mark 37 cumulative rows as `calc`, representing 13 unique variables, but their calculation-expression cells are blank. These fields are therefore displayed as unavailable calculations and are not populated by LipoScope. See `validation/ccrf_calculated_fields.json`.

## Completion measure

The displayed completion percentage is a LipoScope workspace measure calculated as completed currently applicable required response fields divided by currently applicable required response fields that can be assessed locally. It is separate from the Foundation's published CDE count. Identifier fields excluded from local storage and inactive conditional fields do not enter the locally assessable denominator.

## Exports

The research package can contain coded data, readable labels, paired codes and labels, long-format records, the data dictionary, a data-quality report and a source manifest. Identifier and file values are blank. Stored responses in inactive branches remain available but are marked in the data-quality file unless cleared before export.
