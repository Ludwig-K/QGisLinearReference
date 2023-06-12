<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="de_DE" sourcelanguage="en_US">
<context>
    <name>CheckFlags</name>
    <message>
        <location filename="../map_tools/PolEvt.py" line="695"/>
        <source>please select an entry from the list above...</source>
        <translation>Bitte ein Element der obigen Liste auswählen...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="642"/>
        <source>Configuration &apos;{setting_label}&apos; restored...</source>
        <translation>Konfiguration &apos;{setting_label}&apos; wiederhergestellt...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="706"/>
        <source>Delete Configuration &apos;{setting_label}&apos;?</source>
        <translation>Konfiguration &apos;{setting_label}&apos; löschen?</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="719"/>
        <source>Configuration &apos;{setting_label}&apos; deleted...</source>
        <translation>Konfiguration &apos;{setting_label}&apos; gelöscht...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2903"/>
        <source>Canceled by user...</source>
        <translation>Abbruch durch Anwender...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2568"/>
        <source>LinearReferencing ({gdp()})</source>
        <translation>LinearReferencing ({gdp()})</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="745"/>
        <source>Label for Configuration:</source>
        <translation>Name für Konfiguration:</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="758"/>
        <source>Replace stored Configuration &apos;{new_label}&apos;?</source>
        <translation>Gespeicherte Konfiguration &apos;{new_label}&apos; überschreiben?</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="783"/>
        <source>number of stored settings exceeds maximum ({self._num_storable_settings}), please replace existing one...</source>
        <translation>Die Anzahl der gespeicherten Einstellungen überschreitet das Maximum ({self._num_storable_settings}), bitte ersetzen Sie eine vorhandene...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="799"/>
        <source>Current configuration stored under &apos;{new_label}&apos;...</source>
        <translation>Aktuelle Konfiguration unter &apos;{new_label}&apos; gespeichert...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1014"/>
        <source>No valid reference-feature with fid &apos;{ref_fid}&apos;</source>
        <translation>Kein Linien-Feature mit FID &apos;{ref_fid}&apos;</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1091"/>
        <source>no reference-feature with ID &apos;{data_feature[self.ds.dataLyrReferenceField.name()]}&apos; in layer {self.ds.refLyr.name()}</source>
        <translation>Kein Linien-Feature mit FID &apos;{ref_fid}&apos;</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1094"/>
        <source>no feature with ID &apos;{edit_pk}&apos; in layer {self.ds.dataLyr.name()}</source>
        <translation>Kein Feature mit ID &apos;{edit_pk}&apos; in Layer {self.ds.dataLyr.name()}</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1246"/>
        <source>Missing requirements, reference-, data- and show-layer required...</source>
        <translation>Fehlende Voraussetzungen: Referenz-, Daten- und Darstellungs-Layer erforderlich...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1158"/>
        <source>No selection in data-layer...</source>
        <translation>Keine Selektion im Data-Layer...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1226"/>
        <source>no extent calculable for these features</source>
        <translation>Kein Extent für diese Features ermittelbar</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1244"/>
        <source>No selection in show-layer...</source>
        <translation>Keine Selektion im Darstellungs-Layer...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2758"/>
        <source>Referenced Linestring-Geometry &apos;{self.rs.snapped_ref_fid}&apos; in Layer &apos;{self.ds.refLyr.name()}&apos; is multi-part ({ref_feature.geometry().constGet().partCount()} parts), measured Point-on-Line-Feature may be invisible in Show-Layer</source>
        <translation>Die Referenz-Linie besteht aus mehrere Teilen ({ref_feature.geometry().constGet().partCount()} parts), das PoL-Feature wird möglicherweise nicht angezeigt</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1311"/>
        <source>Feature with ID &apos;{self.rs.edit_pk}&apos; successfully updated in &apos;{self.ds.dataLyr.name()}&apos;...</source>
        <translation>Datensatz mit ID &apos;{self.rs.edit_pk}&apos; wurde aktualisiert...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1317"/>
        <source>Update feature failed, measure out of range 0 ... {update_ref_feature.geometry().length()}</source>
        <translation>Speicherung des Datensatzes fehlgeschlagen, Stationierung außerhalb Wertebereich 0 ... {update_ref_feature.geometry().length()}</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1320"/>
        <source>Update feature failed, no reference-feature with PK &apos;{updare_ref_pk}&apos; in layer &apos;{self.ds.refLyr.name()}&apos; ...</source>
        <translation>Speicherung fehlgeschlagen, keine Referenz-Linie mit ID  &apos;{updare_ref_pk}&apos; in Layer &apos;{self.ds.refLyr.name()}&apos; ...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1329"/>
        <source>Update feature failed, no feature &apos;{self.rs.edit_pk}&apos; in layer &apos;{self.ds.dataLyr.name()}&apos; or reference-feature &apos;{self.rs.snapped_ref_fid}&apos; in layer &apos;{self.ds.refLyr.name()}&apos; ...</source>
        <translation>Speicherung, fehlgeschlagen, kein Datensatz mit ID &apos;{self.rs.edit_pk}&apos; in Layer &apos;{self.ds.dataLyr.name()}&apos; oder Referenz-Linie &apos;{self.rs.snapped_ref_fid}&apos; in Layer &apos;{self.ds.refLyr.name()}&apos; ...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1331"/>
        <source>Update feature failed, missing privileges in layer &apos;{self.ds.dataLyr.name()}&apos;...</source>
        <translation>Speicherung fehlgeschlagen, fehlende Berechtigung in Layer &apos;{self.ds.dataLyr.name()}&apos;...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1394"/>
        <source>Expression &apos;{dlg.expressionText()}&apos; valid and used as DisplayExpression for layer &apos;{self.ds.refLyr.name()}&apos;</source>
        <translation>Ausdruck &apos;{dlg.expressionText()}&apos; wird als DisplayExpression für Layer &apos;{self.ds.refLyr.name()}&apos; verwendet</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1396"/>
        <source>Expression &apos;{dlg.expressionText()}&apos; invalid and not used as DisplayExpression for layer &apos;{self.ds.refLyr.name()}&apos;, please check syntax!</source>
        <translation>Ausdruck &apos;{dlg.expressionText()}&apos; fehlerhaft, bitte Syntax prüfen!</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1399"/>
        <source>No reference-layer defined yet</source>
        <translation>Referenz-Layer noch nicht definiert</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1413"/>
        <source>Expression &apos;{dlg.expressionText()}&apos; valid and used as DisplayExpression for layer &apos;{self.ds.dataLyr.name()}&apos;</source>
        <translation>Ausdruck &apos;{dlg.expressionText()}&apos; wird als DisplayExpression für Layer &apos;{self.ds.dataLyr.name()}&apos; verwendet</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1415"/>
        <source>Expression &apos;{dlg.expressionText()}&apos; invalid and not used as DisplayExpression for layer &apos;{self.ds.dataLyr.name()}&apos;, please check syntax!</source>
        <translation>Ausdruck &apos;{dlg.expressionText()}&apos; fehlerhaft, bitte Syntax prüfen!</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1418"/>
        <source>No data-layer defined yet</source>
        <translation>Daten-Layer noch nicht definiert</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1432"/>
        <source>Expression &apos;{dlg.expressionText()}&apos; valid and used as DisplayExpression for layer &apos;{self.ds.showLyr.name()}&apos;</source>
        <translation>Ausdruck &apos;{dlg.expressionText()}&apos; wird als DisplayExpression für Layer &apos;{self.ds.showLyr.name()}&apos; verwendet</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1434"/>
        <source>Expression &apos;{dlg.expressionText()}&apos; invalid and not used as DisplayExpression for layer &apos;{self.ds.showLyr.name()}&apos;, please check syntax!</source>
        <translation>Ausdruck &apos;{dlg.expressionText()}&apos; fehlerhaft, bitte Syntax prüfen!</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1437"/>
        <source>No show-layer defined yet</source>
        <translation>Darstellungs-Layer noch nicht definiert</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1728"/>
        <source>Reference-layer &apos;{reference_layer.name()}&apos; is of type &apos;{wkb_label}&apos;, Point-on-Line-Features on multi-lines are not shown</source>
        <translation>Referenz-Layer &apos;{reference_layer.name()}&apos; hat den Geometrie-Typ &apos;{wkb_label}&apos;, Point-on-Line-Features auf multi-Linien nicht darstellbar</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1930"/>
        <source>Source-Format of chosen data-layer &apos;{data_layer.name()}&apos; is a file-based office-format (*.xlsx/*.odf), this not recommended...</source>
        <translation>Die Quelle des Layers  &apos;{data_layer.name()}&apos; ist ein dateibasiertes Office-Format (*.xlsx/*.odf), das ist nicht empfehlenswert...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2343"/>
        <source>Missing requirements: No show-layer configured...</source>
        <translation>Fehlende Voraussetzungen: Kein Darstellungs-Layer definiert...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2444"/>
        <source>LinearReferencing: Create Point-on-Line-Data-Layer</source>
        <translation>LinearReferencing: Point-on-Line-Data-Layer anlegen</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2475"/>
        <source>Name for Table in GeoPackage:</source>
        <translation>Tabellen-Name im GeoPackage:</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2677"/>
        <source>Canceled by user</source>
        <translation>Abbruch durch Anwender</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2538"/>
        <source>create table &apos;{gpkg_path}&apos;.&apos;{table_name}&apos; successful</source>
        <translation>Tabelle &apos;{gpkg_path}&apos;.&apos;{table_name}&apos; wurde angelegt</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2542"/>
        <source>Error creating data-layer &apos;{gpkg_path}&apos;.&apos;{table_name}&apos;, created layer not valid</source>
        <translation>Fehler beim Anlegen des Layers &apos;{gpkg_path}&apos;.&apos;{table_name}&apos;</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2546"/>
        <source>Error creating data-layer &apos;{gpkg_path}&apos;.&apos;{table_name}&apos;: {writer.errorMessage()}</source>
        <translation>Fehler beim Anlegen des Layers &apos;{gpkg_path}&apos;.&apos;{table_name}&apos;: {writer.errorMessage()}</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2548"/>
        <source>missing requirements...</source>
        <translation>Fehlende Voraussetzungen...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2568"/>
        <source>Name for Virtual Layer:</source>
        <translation>Name für den virtuellen Layer:</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2672"/>
        <source>Virtual layer created and added...</source>
        <translation>Virtueller Layer erzeugt und hinzugefügt...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2675"/>
        <source>Error creating virtual layer...</source>
        <translation>Fehler beim Anlegen des virtuellen Layers...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2679"/>
        <source>first create or configure reference- and data-layer</source>
        <translation>Bitte zuerst Referenz- und Datenlayer anlegen oder einrichten</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2754"/>
        <source>Feature with ID {self.rs.snapped_ref_fid} in Layer &apos;{self.ds.refLyr.name()}&apos; has no value in ID-field {self.ds.refLyrPkField.name()}</source>
        <translation>Datensatz mit FID {self.rs.snapped_ref_fid} in Layer &apos;{self.ds.refLyr.name()}&apos; ohne Referenz-Wert in Feld {self.ds.refLyrPkField.name()}</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2760"/>
        <source>No reference-feature with ID {self.rs.snapped_ref_fid} in layer &apos;{self.ds.refLyr.name()}&apos;</source>
        <translation>Kein Datensatz mit ID {self.rs.snapped_ref_fid} in Layer &apos;{self.ds.refLyr.name()}&apos;</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2811"/>
        <source>New feature with ID &apos;{used_pk}&apos; successfully added to &apos;{self.ds.dataLyr.name()}&apos;...</source>
        <translation>Datensatz mit ID &apos;{used_pk}&apos; in Layer &apos;{self.ds.dataLyr.name()}&apos; hinzugefügt...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2824"/>
        <source>Add feature failed, missing privileges in layer &apos;{self.ds.dataLyr.name()}&apos;...</source>
        <translation>Datensatz in Layer &apos;{self.ds.dataLyr.name()}&apos; konnte nicht angelegt werden, fehlende Privilegien...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2876"/>
        <source>Delete Feature with id &apos;{self.rs.edit_pk}&apos; from layer &apos;{self.ds.dataLyr.name()}&apos;?</source>
        <translation>Datensatz mit ID &apos;{self.rs.edit_pk}&apos; in Layer &apos;{self.ds.dataLyr.name()}&apos; löschen?</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2890"/>
        <source>Feature with ID &apos;{self.rs.edit_pk}&apos; successfully deleted in &apos;{self.ds.dataLyr.name()}&apos;...</source>
        <translation>Datensatz mit ID &apos;{self.rs.edit_pk}&apos; in Layer &apos;{self.ds.dataLyr.name()}&apos; gelöscht...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2906"/>
        <source>Delete feature failed, no feature &apos;{self.rs.edit_pk}&apos; in layer &apos;{self.ds.dataLyr.name()}&apos;...</source>
        <translation>Löschen des Datensatzes fehlgeschlagen, kein Datensatz mit ID &apos;{self.rs.edit_pk}&apos; in Layer &apos;{self.ds.dataLyr.name()}&apos; oder kein referenzierter-Datensatz &apos;{self.rs.snapped_ref_fid}&apos; in Layer &apos;{self.ds.refLyr.name()}&apos; ...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2909"/>
        <source>Delete feature failed, missing privileges in layer &apos;{self.ds.dataLyr.name()}&apos;...</source>
        <translation>Datensatz in Layer &apos;{self.ds.dataLyr.name()}&apos; konnte nicht gelöscht werden, fehlende Privilegien...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2912"/>
        <source>Delete feature failed, no feature selected...</source>
        <translation>Löschen fehlgeschlagen, kein Datensatz selektiert...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="3004"/>
        <source>tool_mode &apos;{tool_mode}&apos; not implemented...</source>
        <translation>tool_mode &apos;{tool_mode}&apos; nicht implementiert...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="3748"/>
        <source>Remove Feature from Selection</source>
        <translation>Datensatz aus Auswahl entfernen</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="3757"/>
        <source>Highlight Feature and Select for Edit</source>
        <translation>Datensatz hervorheben und zur Bearbeitung selektieren</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="3766"/>
        <source>Pan to Feature and Select for Edit</source>
        <translation>Auf Datensatz zoomen und zur Bearbeitung selektieren</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="3775"/>
        <source>Show Feature-Form</source>
        <translation>Datensatz-Formular öffnen</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="3802"/>
        <source>Highlight Reference-Feature</source>
        <translation>Linien-Shape hervorheben</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="3811"/>
        <source>Zoom to Reference-Feature</source>
        <translation>Auf Linien-Shape zoomen</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="3820"/>
        <source>Show Reference-Feature-Form</source>
        <translation>Datensatz-Formular Referenzlayer öffnen</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="3847"/>
        <source>Show Show-Feature-Form</source>
        <translation>Datensatz-Formular Darstellungs-Layer öffnen</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="3919"/>
        <source>no feature with ID &apos;{edit_pk}&apos; in data-layer {self.ds.dataLyr.name()}</source>
        <translation>Kein Datensatz mit ID &apos;{edit_pk}&apos; in Layer {self.ds.dataLyr.name()}</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="3957"/>
        <source>no feature with value &apos;{edit_pk}&apos; in back-reference-field &apos;{self.ds.showLyrBackReferenceField.name()}&apos; of show-layer &apos;{self.ds.showLyr.name()}&apos;</source>
        <translation>Kein Datensatz mit Wert &apos;{edit_pk}&apos; im Rück-Referenz-Feld &apos;{self.ds.showLyrBackReferenceField.name()}&apos; des Layers &apos;{self.ds.showLyr.name()}&apos;</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="4003"/>
        <source>no feature with value &apos;{data_feature[self.ds.dataLyrReferenceField.name()]}&apos; in field &apos;{self.ds.dataLyrReferenceField.name()}&apos; of layer &apos;{self.ds.refLyr.name()}&apos;</source>
        <translation>Kein Datensatz mit Wert  &apos;{data_feature[self.ds.dataLyrReferenceField.name()]}&apos; im Feld &apos;{self.ds.dataLyrReferenceField.name()}&apos; des Layers &apos;{self.ds.refLyr.name()}&apos;</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="4001"/>
        <source>Reference-feature without geometry (layer &apos;{self.ds.refLyr.name()}&apos;, field &apos;{self.ds.dataLyrReferenceField.name()}&apos;, value &apos;{data_feature[self.ds.dataLyrReferenceField.name()]}&apos;)</source>
        <translation>Referenz-Datensatz ohne Geometrie (Layer &apos;{self.ds.refLyr.name()}&apos;, Field &apos;{self.ds.dataLyrReferenceField.name()}&apos;, Wert &apos;{data_feature[self.ds.dataLyrReferenceField.name()]}&apos;)</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1360"/>
        <source>Feature with FID &apos;{ref_fid}&apos; in reference-layer &apos;{self.ds.refLyr.name()}&apos; not found or not valid</source>
        <translation>Datensatz mit FID &apos;{ref_fid}&apos; in Referenz-Layer &apos;{self.ds.refLyr.name()}&apos; nicht vorhanden oder valide</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1546"/>
        <source>Feature with fid &apos;{ref_fid}&apos; not found, not valid or without geometry</source>
        <translation>Referenz-Datensatz mit FID &apos;{ref_fid}&apos; nicht vorhanden, valide oder ohne Geometrie</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="385"/>
        <source>Initializing, please wait...</source>
        <translation>Initialisierung, bitte warten...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="387"/>
        <source>hover and click on reference-line to show coords and measures...</source>
        <translation>Cursor über Referenzlinie führen, zur Messung klicken...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="388"/>
        <source>Point on reference-line measured, edit, add feature or click again to resume...</source>
        <translation>Stationierung berechnet: Punkt bearbeiten und gegebenenfalls speichern, Canvas-Klick für neue Messung...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="389"/>
        <source>grab point on canvas and move it to desired position on selected line</source>
        <translation>Punkt auf Karte zur gewünschten Position verschieben</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="390"/>
        <source>hold mouse-button, move grabbed point to desired position and release</source>
        <translation>Cursor mit gedrückter Maustaste zur Zielposition führen und dort loslassen</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="392"/>
        <source>no reference-layer (linestring) found or configured...</source>
        <translation>kein Referenzlayer konfiguriert...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="393"/>
        <source>click or draw rect to select features [ctrl] â remove from Feature-Selection [shift] â add to Feature-Selection [-] â replace Feature-Selection</source>
        <translation>Features auswählen (Punkt/Rechteck) [ctrl] ➜ aus Selektionsliste entfernen [shift] ➜ hinzufügen [-] ➜ ersetzen</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="394"/>
        <source>hover and click on reference-line to reposition selected feature, click &apos;update&apos; to save feature...</source>
        <translation>Selektiertes Feature neu positionieren und speichern...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="395"/>
        <source>selected feature repositioned, click &apos;update&apos; to save...</source>
        <translation>selektiertes Feature neu positioniert, jetzt speichern...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="591"/>
        <source>No completed measure yet...</source>
        <translation>Keine abgeschlossene Messung...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2855"/>
        <source>Layer &apos;{self.ds.dataLyr.name()}&apos; is editable!

[Yes]        â End edit session with save
[No]         â End edit session without save 
[Cancel]  â Quit...</source>
        <translation>La couche &apos;{self.ds.dataLyr.name()}&apos; est modifiable 

[Ja] ➜ Änderungen speichern und fortfahren
[Nein] ➜ Änderungen verwerfen und fortfahren
[Cancel] ➜ Abbruch...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1945"/>
        <source>not allowed capabilities: {caps_string}
 ➜ Some editing options will not be available</source>
        <translation>Fehlende Privilegien: {caps_string}
 ➜ Einige Editier-Optionen werden nicht verfügbar sein</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2481"/>
        <source>Table &apos;{table_name}&apos; already exists in {gpkg_path} !

Replace?</source>
        <translation>Tabelle &apos;{table_name}&apos; bereits vorhanden in &apos;{gpkg_path}&apos;!

Ersetzen?</translation>
    </message>
</context>
<context>
    <name>LinearReference</name>
    <message>
        <location filename="../LinearReference.py" line="149"/>
        <source>&lt;b&gt;LinearReferencing&lt;/b&gt;&lt;hr&gt;Measure and Digitize Point-on-Line Features</source>
        <translation>&amp;lt;b&amp;gt;LinearReferencing&amp;lt;/b&amp;gt;&amp;lt;hr&amp;gt;Point-on-Line Features messen und digitalisieren</translation>
    </message>
    <message>
        <location filename="../LinearReference.py" line="159"/>
        <source>&lt;b&gt;LinearReferencing&lt;/b&gt;&lt;hr&gt;Measure and Digitize Line-on-Line Features</source>
        <translation>&amp;lt;b&amp;gt;LinearReferencing&amp;lt;/b&amp;gt;&amp;lt;hr&amp;gt;Line-on-Line Features messen und digitalisieren</translation>
    </message>
    <message>
        <location filename="../LinearReference.py" line="169"/>
        <source>&lt;b&gt;LinearReferencing&lt;/b&gt;&lt;hr&gt;Show Help</source>
        <translation>&amp;lt;b&amp;gt;LinearReferencing&amp;lt;/b&amp;gt;&amp;lt;hr&amp;gt;Hilfe aufrufen</translation>
    </message>
</context>
<context>
    <name>LolDialog</name>
    <message>
        <location filename="../dialogs/LolDialog.py" line="58"/>
        <source>Linear Referencing: Line-on-Line</source>
        <translation>Linear Referencing: Line-on-Line</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="107"/>
        <source>toggle window dockable/undockable</source>
        <translation>Fenster andocken/lösen</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="119"/>
        <source>Measure:</source>
        <translation>Messen:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="848"/>
        <source>Reference-Line:</source>
        <translation>Referenz-Linie:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="151"/>
        <source>Open Form</source>
        <translation>Formular öffnen</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="160"/>
        <source>Zoom to Feature</source>
        <translation>Auf Datensatz zoomen</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="165"/>
        <source>Offset:</source>
        <translation>Offset:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="190"/>
        <source>From:</source>
        <translation>Von:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="191"/>
        <source>To:</source>
        <translation>Bis:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="206"/>
        <source>Snapped Point x/y:</source>
        <translation>Snapped-Point x/y:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="224"/>
        <source>Measure (abs / fract):</source>
        <translation>Stationierung (abs/fract):</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="233"/>
        <source>Measure-From as percentage
 - range 0...100</source>
        <translation>Stationierung Start-Punkt prozentual
 - Wertebereich 0...100</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="245"/>
        <source>Measure-To as percentage
 - range 0...100</source>
        <translation>Stationierung End-Punkt prozentual
 - Wertebereich 0...100</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="255"/>
        <source>Distance</source>
        <translation>Abschnitt</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="264"/>
        <source>moves segment to reference-line-start-point</source>
        <translation>Abschnitt zum Anfang der Referenzlinie verschieben</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="271"/>
        <source>&apos;prepend&apos; segment (new to-measure == old from-measure)</source>
        <translation>Abschnitt in Richtung Startpunkt verschieben (neue Stationierung-Bis == alte Stationierung-Von)</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="286"/>
        <source>enlarge/shrink segment
   - keeps From-Point, moves To-Point
   - units accordingly Layer-Projection
   - ctrl/shift/ctrl+shift spinbutton-click-modifiers with factors 10/100/1000</source>
        <translation>Segment verkleinern/vergrößern
     Startpunkt bleibt erhalten, Endpunkt wird verschoben
     Einheiten passend zur Layer-Projektion
     ctrl/shift/ctrl+shift Klick auf Spinbuttons ➜ Faktor 10/100/1000</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="303"/>
        <source>&apos;append&apos; segment (new from-measure == old to-measure)</source>
        <translation>Abschnitt in Richtung Endpunkt verschieben (neue Stationierung-Von == alte Stationierung-Bis)</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="310"/>
        <source>move segment to reference-line-end-point</source>
        <translation>Abschnitt zum Endpunkt der Referenzlinie verschieben</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="319"/>
        <source>zoom to segment</source>
        <translation>auf Abschnitt zoomen</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="331"/>
        <source>move From-Point</source>
        <translation>Start-Punkt verschieben</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="335"/>
        <source>move From-Point by mouse-down and drag on selected reference-line</source>
        <translation>Start-Punkt auf Karte verschieben</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="339"/>
        <source>move To-Point</source>
        <translation>Endpunkt verschieben</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="343"/>
        <source>move To-Point by mouse-down and drag on selected reference-line</source>
        <translation>Endpunkt auf Karte verschieben</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="350"/>
        <source>Move segment</source>
        <translation>Abschnitt verschieben</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="354"/>
        <source>Move segment interactive:
   [-]	-&gt; change measure, keep offset
 [shift]	-&gt; change offset, keep measure
  [ctrl]	-&gt; change offset and measure</source>
        <translation>Abschnitt auf Karte verschieben:
   [ - ]	➜ Stationierung
   [shift]	➜ Abstand
   [ctrl]	➜ Abstand und Stationierung</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="361"/>
        <source>Resume measure</source>
        <translation>neue Messung</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="364"/>
        <source>Reset results and start new measure</source>
        <translation>Ergebnisse zurücksetzen, neue Messung</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="372"/>
        <source>Edit:</source>
        <translation>Bearbeiten:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="380"/>
        <source>Selected PK:</source>
        <translation>Selektierter Datensatz:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="390"/>
        <source>Update</source>
        <translation>Speichern</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="393"/>
        <source>Update selected feature...</source>
        <translation>selektierten Datensatz speichern...</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="398"/>
        <source>Insert</source>
        <translation>Hinzufügen</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="401"/>
        <source>Insert feature / duplicate selected feature...</source>
        <translation>Datensatz hinzufügen oder duplizieren...</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="406"/>
        <source>Delete</source>
        <translation>Löschen</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="409"/>
        <source>Delete selected feature...</source>
        <translation>selektierten Datensatz löschen...</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="416"/>
        <source>Feature-Selection:</source>
        <translation>Editier-Selektion:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="431"/>
        <source>Select Feature(s)</source>
        <translation>Features auswählen</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="434"/>
        <source>Select Features from Show-Layer
    click (point) or drag (rectangle)
    [Shift] â append
    [Ctrl] â remove</source>
        <translation>Datensätze des Darstellungs-Layers auswählen
    Punkt (Einzel-) oder Rechteck (Mehrfachselektion)
    [Shift] ➜ Datensätze hinzufügen
    [Ctrl] ➜ Datensätze entfernen</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="439"/>
        <source>Insert all Features</source>
        <translation>Alle Datensätze des Daten-Layers hinzufügen</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="442"/>
        <source>Insert all Features from Data-Layer
    [Shift] â append</source>
        <translation>Alle Datensätze des Daten Layers hinzufügen
    [Shift] ➜ Selektion erweitern</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="447"/>
        <source>Insert selected Data-Layer-Features</source>
        <translation>Selektierte Features des Datenlayer hinzufügen</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="450"/>
        <source>Insert selected Features from Data-Layer
    [Shift] â append</source>
        <translation>Selektierte Features des Datenlayer hinzufügen
    [Shift] ➜ Selektion erweitern</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="455"/>
        <source>Insert selected Show-Layer-Features</source>
        <translation>Selektierte Features des Darstellungs-Layers hinzufügen</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="458"/>
        <source>Insert selected Features from Show-Layer
    [Shift] â append</source>
        <translation>Selektierte Features des Darstellungs-Layers hinzufügen
    [Shift] ➜ Selektion erweitern</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="492"/>
        <source>Zoom to feature-selection</source>
        <translation>Auf Selektion zoomen</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="495"/>
        <source>Zoom to selected features</source>
        <translation>Auf Selektion zoomen</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="499"/>
        <source>Clear Feature-Selection</source>
        <translation>Selektion zurücksetzen</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="514"/>
        <source>Layers and Fields:</source>
        <translation>Layer und Felder:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="520"/>
        <source>Reference-Layer...</source>
        <translation>Referenz-Layer...</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="534"/>
        <source>Reference-layer, provides linestring-geometries
  geometry-Type linestring/m/z
  multi-linestring/m/z</source>
        <translation>Referenz-Layer, liefert linestring-Geometrien, Geometrie-Typ
   linestring/m/z
   multi-linestring/m/z</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="729"/>
        <source>Open Table</source>
        <translation>Tabelle öffnen</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="738"/>
        <source>Edit Display-Expression for this Layer</source>
        <translation>DIsplay-Ausdruck dieses Layers bearbeiten</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="616"/>
        <source>      ... ID-Field:</source>
        <translation>      ... ID-Spalte:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="570"/>
        <source>Identifier-Field, used for assignment to Data-Layer
   type integer or string, unique, not null
   typically the PK-Field</source>
        <translation>Referenz-Feld zum Daten-Layer
   integer oder string, unique, not null
   üblicherweise das PK-Feld</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="574"/>
        <source>Data-Layer...</source>
        <translation>Daten-Layer...</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="588"/>
        <source>Layer for storing the attributes of Line-on-Line-features:
   geometry-less
   Editable
Required Fields:
   ID-Field (PK)
   Reference-Field
   Measure-From-Field
   Measure-To-Field
   Offset-Field</source>
        <translation>Layer der Line-on-Line-Features:
   geometrie-los
   editierbar
Notwendige Spalten:
   ID (PK)
   Referenz zum Linienlayer
   Stationierung von
   Stationierung bis
   Abstand</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="742"/>
        <source>...or create</source>
        <translation>...oder anlegen</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="612"/>
        <source>Create a non-geometry GPKG-Layer for storing measure-data</source>
        <translation>Einen geometrielosen GPKG-Layer für die Line-on-Line-Features anlegen</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="630"/>
        <source>Field with unique key,
   type integer or string
   typically the PK-Field</source>
        <translation>ID-Feld
   unique, not null
   integer oder string
   üblicherweise das PK-Feld</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="634"/>
        <source>      ... Reference-Field:</source>
        <translation>      ... Referenz-Feld:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="648"/>
        <source>Field for assignment to Reference-Layer
   type matching to Reference-Layer-ID-Field</source>
        <translation>Zuordnungsfeld zum Referenz-Layer
   passender Daten-Typ</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="652"/>
        <source>      ... Measure-From-Field:</source>
        <translation>      ... Stationierung von:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="666"/>
        <source>Field for storing measure-from
   distance of segment-start to startpoint of assigned line
   numeric type</source>
        <translation>Feld für Stationierung-von
   Entfernung zum Startpunkt des zugeordneten Linien-Features
   numerischer Typ</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="670"/>
        <source>      ... Measure-To-Field:</source>
        <translation>      ... Stationierung bis:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="684"/>
        <source>Field for storing measure-to
   distance of segment-end to startpoint of assigned line
   numeric type</source>
        <translation>Feld für Stationierung-bis
   Entfernung zum Startpunkt des zugeordneten Linien-Features
   numerischer Typ</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="688"/>
        <source>      ... Offset-Field:</source>
        <translation>      ... Abstands-Field:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="702"/>
        <source>Field for storing offset
   offset of the segment to assigned reference-line
   type numeric
Values...
   &gt; 0 â left
   &lt; 0 â right
  = 0 â on reference-line</source>
        <translation>Spalte für den Abstand zur zugeordneten Referenzlinie
   numerischer Typ
   &amp;gt; 0 ➜ links
   &amp;lt; 0 ➜ rechts
  = 0 ➜ auf der Referenz-Linie</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="706"/>
        <source>Show-Layer...</source>
        <translation>Darstellungs-Layer...</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="720"/>
        <source>Layer to show the Line-on-Line-Features
Source-Type:
     virtual (with query to Reference- and  Data-Layer)
     ogr (f.e. view in PostGIS or GPKG)</source>
        <translation>Layer zur Darstellung der Line-on-Line-Features:
     virtueller QGis-Layer mit Abfrage des Referenz- und Daten-Layers
     ogr (z. B. PostGIS- oder GPKG-View)</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="744"/>
        <source>Create a virtual Layer for showing the results</source>
        <translation>virtuellen Darstellungslayer anlegen</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="748"/>
        <source>      ... Back-Reference-Field:</source>
        <translation>      ... Rück-Referenz-Feld:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="762"/>
        <source>Field for Back-Reference to data-layer
   Field-Type and Contents matching to Data-Layer-ID-Field
   typically the PK-Fields in both layers</source>
        <translation>Feld mit Rück-Referenz zum Daten-Layer
   Daten-Typ und Inhalt passend zum ID-Feld des Daten-Layers
   üblicherweise das PK-Feld in beiden Layern</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="769"/>
        <source>Styles:</source>
        <translation>Stile:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="784"/>
        <source>Symbol</source>
        <translation>Symbol</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="785"/>
        <source>Size</source>
        <translation>Größe</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="786"/>
        <source>Width</source>
        <translation>Breite</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="787"/>
        <source>Color</source>
        <translation>Farbe</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="788"/>
        <source>Fill-Color</source>
        <translation>Füll-Farbe</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="792"/>
        <source>From-Point:</source>
        <translation>Start-Punkt:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="813"/>
        <source>To-Point:</source>
        <translation>End-Punkt:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="834"/>
        <source>Segment-Line:</source>
        <translation>Segment-Linie:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="863"/>
        <source>Store/Restore Configurations:</source>
        <translation>Einstellungen speichern/wiederherstellen:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="870"/>
        <source>Stored Configurations:</source>
        <translation>Gespeicherte Einstellungen:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="895"/>
        <source>Measure</source>
        <translation>Messung</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="897"/>
        <source>Settings</source>
        <translation>Einstellungen</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="878"/>
        <source>Store current configuration...</source>
        <translation>Aktuelle Einstellungen speichern...</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="881"/>
        <source>Restore selected configuration...</source>
        <translation>gewählte Konfiguration wiederherstellen...</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="884"/>
        <source>Delete selected configuration...</source>
        <translation>gewählte Konfiguration löschen...</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="178"/>
        <source>Cursor-Position x/y:</source>
        <translation>Cursor-Position x/y:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="169"/>
        <source>Segment-distance to reference-line
   &gt; 0 left
   &lt; 0 right
   ctrl/shift/ctrl+shift spinbutton-click-modifiers with factors 10/100/1000</source>
        <translation>Abstand zwischen Segement und Referenzlinie
   &amp;gt; 0 links
   &amp;lt; 0 rechts
   ctrl/shift/ctrl+shift Klick auf Spinbuttons ➜ Faktor 10/100/1000</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="228"/>
        <source>Measure From-Point
 - range 0...length_of_line
 - units accordingly Layer-Projection
 - ctrl/shift/ctrl+shift click-modifiers with factors 10/100/1000</source>
        <translation>Stationierung Start-Punkt
 - Wertebereich 0...Linienlänge
 - Einheit passend zu Layer-Projektion
 - ctrl/shift/ctrl+shift Klick-➜ Faktor 10/100/1000</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="240"/>
        <source>Measure To-Point
 - range 0...length_of_line
 - units accordingly Layer-Projection
 - ctrl/shift/ctrl+shift spinbutton-click-modifiers with factors 10/100/1000</source>
        <translation>Stationierung des End-Punktes
 - Wertebereich 0...Linienlänge
 - Maßeinheit wie Layer-Projektion
 - ctrl/shift/ctrl+shift Klick-➜ Faktor 10/100/1000</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="281"/>
        <source>move segment towards reference-line-start-point
   - ctrl/shift/ctrl+shift click-modifiers with factors 10/100/1000</source>
        <translation>Segment in Richtung Startpunkt der Referenzlinie verschieben
   - ctrl/shift/ctrl+shift Klick ➜ Faktor 10/100/1000</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="296"/>
        <source>move segment towards reference-line-end-point
   - ctrl/shift/ctrl+shift click-modifiers with factors 10/100/1000</source>
        <translation>Segment in Richtung Endpunkt der Referenzlinie verschieben
   - ctrl/shift/ctrl+shift Klick ➜ Faktor 10/100/1000</translation>
    </message>
</context>
<context>
    <name>PolDialog</name>
    <message>
        <location filename="../dialogs/PolDialog.py" line="58"/>
        <source>Linear Referencing: Point-on-Line</source>
        <translation>Linear Referencing: Point-on-Line</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="106"/>
        <source>toggle window dockable/undockable</source>
        <translation>Fenster andocken/lösen</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="116"/>
        <source>Measure:</source>
        <translation>Messen:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="695"/>
        <source>Reference-Line:</source>
        <translation>Referenz-Linie:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="148"/>
        <source>Open Form</source>
        <translation>Formular öffnen</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="157"/>
        <source>Zoom to Feature</source>
        <translation>Auf Datensatz zoomen</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="187"/>
        <source>Measure (abs/fract):</source>
        <translation>Stationierung (abs/fract):</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="195"/>
        <source>Measure as percentage
 - range 0...100</source>
        <translation>Stationierung prozentual
 - range 0...100</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="265"/>
        <source>Resume measure</source>
        <translation>neue Messung</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="268"/>
        <source>Reset results and start new measure</source>
        <translation>Ergebnisse zurücksetzen, neue Messung</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="274"/>
        <source>Edit:</source>
        <translation>Bearbeiten:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="284"/>
        <source>Edit-PK:</source>
        <translation>Selektierter Datensatz:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="296"/>
        <source>Update</source>
        <translation>Speichern</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="299"/>
        <source>Update selected feature...</source>
        <translation>selektierten Datensatz speichern...</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="303"/>
        <source>Insert</source>
        <translation>Hinzufügen</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="306"/>
        <source>Insert feature / duplicate selected feature...</source>
        <translation>Datensatz hinzufügen oder duplizieren...</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="311"/>
        <source>Delete</source>
        <translation>Löschen</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="314"/>
        <source>Delete selected feature...</source>
        <translation>selektierten Datensatz löschen...</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="321"/>
        <source>Feature-Selection:</source>
        <translation>Editier-Selektion:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="333"/>
        <source>Select Features</source>
        <translation>Features auswählen</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="337"/>
        <source>Select Features from Show-Layer
    click (point) or drag (rectangle)
    [Shift] â append
    [Ctrl] â remove</source>
        <translation>Datensätze des Darstellungs-Layers auswählen
    Punkt (Einzel-) oder Rechteck (Mehrfachselektion)
    [Shift] ➜ Datensätze hinzufügen
    [Ctrl] ➜ Datensätze entfernen</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="342"/>
        <source>Insert all Features</source>
        <translation>Alle Datensätze des Daten-Layers hinzufügen</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="345"/>
        <source>Insert all Features from Data-Layer
    [Shift] â append</source>
        <translation>Alle Datensätze des Daten Layers hinzufügen
    [Shift] ➜ Selektion erweitern</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="350"/>
        <source>Insert selected Data-Layer-Features</source>
        <translation>Selektierte Features des Datenlayer hinzufügen</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="353"/>
        <source>Insert selected Features from Data-Layer
    [Shift] â append</source>
        <translation>Selektierte Features des Datenlayer hinzufügen
    [Shift] ➜ Selektion erweitern</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="358"/>
        <source>Insert selected Show-Layer-Features</source>
        <translation>Selektierte Features des Darstellungs-Layers hinzufügen</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="361"/>
        <source>Insert selected Features from Show-Layer
    [Shift] â append</source>
        <translation>Selektierte Features des Darstellungs-Layers hinzufügen
    [Shift] ➜ Selektion erweitern</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="392"/>
        <source>Zoom to feature-selection</source>
        <translation>Auf Selektion zoomen</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="395"/>
        <source>Zoom to selected features</source>
        <translation>Auf Selektion zoomen</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="399"/>
        <source>Clear Feature-Selection</source>
        <translation>Selektion zurücksetzen</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="419"/>
        <source>Layers and Fields:</source>
        <translation>Layer und Felder:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="425"/>
        <source>Reference-Layer...</source>
        <translation>Referenz-Layer...</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="439"/>
        <source>Linestring-Layer, Geometry-Type linestring/m/z, also Shapfiles with multi-linestring/m/z</source>
        <translation>Referenz-Layer, liefert linestring-Geometrien, Geometrie-Typ
   linestring/m/z
   multi-linestring/m/z</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="594"/>
        <source>Open Table</source>
        <translation>Tabelle öffnen</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="603"/>
        <source>Edit Display-Expression for this Layer</source>
        <translation>DIsplay-Ausdruck dieses Layers bearbeiten</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="520"/>
        <source>      ... ID-Field:</source>
        <translation>      ... ID-Spalte:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="476"/>
        <source>Field for assignment-key to Data-Layer
type integer or string, typically the PK-Field</source>
        <translation>Referenz-Feld zum Daten-Layer
   integer oder string, unique, not null
   üblicherweise das PK-Feld</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="479"/>
        <source>Data-Layer...</source>
        <translation>Daten-Layer...</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="494"/>
        <source>Geometryless Layer for storing the attributes of point-on-line-features:
	- Reference-Field
	- Measure-Field
Must have a single-column PK</source>
        <translation>Layer der Point-on-Line-Features:
   geometrie-los
   editierbar
Notwendige Spalten:
   ID (PK)
   Referenz zum Linienlayer
   Stationierung</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="607"/>
        <source>...or create</source>
        <translation>...oder anlegen</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="517"/>
        <source>Create a non-geometry GPKG-Layer for storing measure-data</source>
        <translation>Einen geometrielosen GPKG-Layer für die Point-on-Line-Features anlegen</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="534"/>
        <source>Field with unique key,
type integer or string, typically the PK-Field</source>
        <translation>ID-Feld
   unique, not null
   integer oder string
   üblicherweise das PK-Feld</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="537"/>
        <source>      ... Reference-Field:</source>
        <translation>      ... Referenz-Feld:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="551"/>
        <source>Field for storing the assignment-key to Reference-Layer
type matching to Reference-Layer-ID-Field</source>
        <translation>Feld für Zuordnung zum Referenz-Layer
Datentyp passend zum Referenz-Layer-ID-Feld</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="554"/>
        <source>      ... Measure-Field:</source>
        <translation>      ... Stationierungs-Feld:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="568"/>
        <source>Field for storing measure
â distance to the startpoint of the assigned line
numeric data-type</source>
        <translation>Feld für Stationierung
   Entfernung zum Startpunkt des zugeordneten Linien-Features
   numerischer Typ</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="571"/>
        <source>Show-Layer...</source>
        <translation>Darstellungs-Layer...</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="585"/>
        <source>Layer to show the point-on-line-Features
Geometry-Type POINT
Source-Type: virtual or ogr (f.e. view in PostGIS or GPKG)</source>
        <translation>Layer zur Darstellung der Point-on-Line-Features:
     virtueller QGis-Layer mit Abfrage des Referenz- und Daten-Layers
     ogr (z. B. PostGIS- oder GPKG-View)</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="608"/>
        <source>Create a virtual Layer for showing the results</source>
        <translation>virtuellen Darstellungslayer anlegen</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="611"/>
        <source>      ... Back-Reference-Field:</source>
        <translation>      ... Rück-Referenz-Feld:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="625"/>
        <source>Field for Back-Reference to data-layer
Field-Type and contents matching to Data-Layer-ID-Field
typically the PK-Fields in both layers</source>
        <translation>Feld mit Rück-Referenz zum Daten-Layer
   Daten-Typ und Inhalt passend zum ID-Feld des Daten-Layers
   üblicherweise das PK-Feld in beiden Layern</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="630"/>
        <source>Styles:</source>
        <translation>Stile:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="645"/>
        <source>Symbol</source>
        <translation>Symbol</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="646"/>
        <source>Size</source>
        <translation>Größe</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="647"/>
        <source>Width</source>
        <translation>Breite</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="648"/>
        <source>Color</source>
        <translation>Farbe</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="649"/>
        <source>Fill-Color</source>
        <translation>Füll-Farbe</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="653"/>
        <source>Measure-Point:</source>
        <translation>Stationierungspunkt:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="675"/>
        <source>Edit-Point:</source>
        <translation>Editier-Marker:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="710"/>
        <source>Store/Restore Configurations:</source>
        <translation>Einstellungen speichern/wiederherstellen:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="717"/>
        <source>Stored Configurations:</source>
        <translation>Gespeicherte Einstellungen:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="741"/>
        <source>Measure</source>
        <translation>Messung</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="742"/>
        <source>Settings</source>
        <translation>Einstellungen</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="725"/>
        <source>Store current configuration...</source>
        <translation>Aktuelle Einstellungen speichern...</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="728"/>
        <source>Restore selected configuration...</source>
        <translation>gewählte Konfiguration wiederherstellen...</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="731"/>
        <source>Delete selected configuration...</source>
        <translation>gewählte Konfiguration löschen...</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="163"/>
        <source>Cursor-Position x/y:</source>
        <translation>Cursor-Position x/y:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="258"/>
        <source>pan to measure</source>
        <translation>auf Punkt zentrieren</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="175"/>
        <source>Snapped-Position x/y:</source>
        <translation>Stationierungspunkt x/y:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="190"/>
        <source>Measure in real-world units
 - range 0...length_of_line
 - units accordingly Layer-Projection
 - ctrl/shift/ctrl+shift spinbutton-click-modifiers with factors 10/100/1000</source>
        <translation>Abstand zum Starpunkt der Referenzlinie
 - Wertebereich 0...Linienlänge
 - Einheit passend zur Layer-Projection
 - ctrl/shift/ctrl+shift Klick-➜ Faktor 10/100/1000</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="214"/>
        <source>moves segment to reference-line-start-point</source>
        <translation>Abschnitt zum Anfang der Referenzlinie verschieben</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="224"/>
        <source>move segment towards reference-line-start-point
   - ctrl/shift/ctrl+shift click-modifiers with factors 10/100/1000</source>
        <translation>Segment in RIchtung Startpunkt der Referenzlinie verschieben
   - ctrl/shift/ctrl+shift Klick-➜ Faktor10/100/1000</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="228"/>
        <source>move Point</source>
        <translation>Punkt verschieben</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="232"/>
        <source>move To-Point by mouse-down and drag on selected reference-line</source>
        <translation>Endpunkt auf Referenzlinie verschieben</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="242"/>
        <source>move segment towards reference-line-end-point
   - ctrl/shift/ctrl+shift click-modifiers with factors 10/100/1000</source>
        <translation>Segment in RIchtung Endpunkt der Referenzlinie verschieben
   - ctrl/shift/ctrl+shift Klick-➜ Faktor10/100/1000</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="249"/>
        <source>move segment to reference-line-end-point</source>
        <translation>Abschnitt zum Endpunkt der Referenzlinie verschieben</translation>
    </message>
</context>
<context>
    <name>RuntimeSettings</name>
    <message>
        <location filename="../map_tools/LolEvt.py" line="711"/>
        <source>please select an entry from the list above...</source>
        <translation>Bitte ein Element der obigen Liste auswählen...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="684"/>
        <source>Configuration &apos;{setting_label}&apos; restored...</source>
        <translation>Konfiguration &apos;{setting_label}&apos; wiederhergestellt...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="722"/>
        <source>Delete Configuration &apos;{setting_label}&apos;?</source>
        <translation>Konfiguration &apos;{setting_label}&apos; löschen?</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="735"/>
        <source>Configuration &apos;{setting_label}&apos; deleted...</source>
        <translation>Konfiguration &apos;{setting_label}&apos; gelöscht...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3376"/>
        <source>Canceled by user...</source>
        <translation>Abbruch durch user...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="2996"/>
        <source>LinearReferencing ({gdp()})</source>
        <translation>LinearReferencing ({gdp()})</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="761"/>
        <source>Label for Configuration:</source>
        <translation>Name für Konfiguration:</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="774"/>
        <source>Replace stored Configuration &apos;{new_label}&apos;?</source>
        <translation>Gespeicherte Konfiguration &apos;{new_label}&apos; überschreiben?</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="799"/>
        <source>number of stored settings exceeds maximum ({self._num_storable_settings}), please replace existing one...</source>
        <translation>Die Anzahl der gespeicherten Einstellungen überschreitet das Maximum ({self._num_storable_settings}), bitte ersetzen Sie eine vorhandene...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="815"/>
        <source>Current configuration stored under &apos;{new_label}&apos;...</source>
        <translation>Aktuelle Konfiguration unter &apos;{new_label}&apos; gespeichert...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1038"/>
        <source>Null-Values in Offset-Field &apos;{self.ds.dataLyr.name()}.{self.ds.dataLyrOffsetField.name()}&apos;, assumed 0...</source>
        <translation>Null-Wert im Offset-Feld &apos;{self.ds.dataLyr.name()}.{self.ds.dataLyrOffsetField.name()}&apos;, Wert 0 angenommen...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1089"/>
        <source>no reference-feature with ID &apos;{data_feature[self.ds.dataLyrReferenceField.name()]}&apos; in layer {self.ds.refLyr.name()}</source>
        <translation>Kein Linien-Feature mit FID &apos;{ref_fid}&apos;</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1091"/>
        <source>no data-feature with ID &apos;{edit_pk}&apos; in layer {self.ds.dataLyr.name()}</source>
        <translation>kein Datensatz mit ID &apos;{edit_pk}&apos; in Layer {self.ds.dataLyr.name()}</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1237"/>
        <source>Missing requirements, reference-, data- and show-layer required...</source>
        <translation>Fehlende Voraussetzungen: Referenz-, Daten- und Darstellungs-Layer erforderlich...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1149"/>
        <source>No selection in data-layer...</source>
        <translation>Keine Selektion im Data-Layer...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1218"/>
        <source>no extent calculable for these features</source>
        <translation>Kein Extent für diese Features ermittelbar</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1235"/>
        <source>No selection in show-layer...</source>
        <translation>Keine Selektion im Darstellungs-Layer...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3298"/>
        <source>Layer &apos;{self.ds.dataLyr.name()}&apos; is editable!

[Yes]        â End edit session with save
[No]         â End edit session without save 
[Cancel]  â Quit...</source>
        <translation>Der Layer &apos;{self.ds.dataLyr.name()}&apos; ist editierbar!

[Ja] ➜ Änerungen speichern und fortfahrenbeenden
[Nein] ➜ Änderungen verwerfen und fortfahren
[Cancel] ➜ Beenden...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1305"/>
        <source>Feature with ID &apos;{self.rs.edit_pk}&apos; successfully updated in &apos;{self.ds.dataLyr.name()}&apos;...</source>
        <translation>Datensatz mit ID &apos;{self.rs.edit_pk}&apos; wurde aktualisiert...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1311"/>
        <source>Update feature failed, measure out of range 0 ... {update_ref_feature.geometry().length()}</source>
        <translation>Speicherung des Datensatzes fehlgeschlagen, Stationierung außerhalb Wertebereich 0 ... {update_ref_feature.geometry().length()}</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1314"/>
        <source>Update feature failed, no reference-feature with PK &apos;{updare_ref_pk}&apos; in layer &apos;{self.ds.refLyr.name()}&apos; ...</source>
        <translation>Speicherung fehlgeschlagen, keine Referenz-Linie mit ID  &apos;{updare_ref_pk}&apos; in Layer &apos;{self.ds.refLyr.name()}&apos; ...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1323"/>
        <source>Update feature failed, no feature &apos;{self.rs.edit_pk}&apos; in layer &apos;{self.ds.dataLyr.name()}&apos; or reference-feature &apos;{self.rs.snapped_ref_fid}&apos; in layer &apos;{self.ds.refLyr.name()}&apos; ...</source>
        <translation>Speicherung, fehlgeschlagen, kein Datensatz mit ID &apos;{self.rs.edit_pk}&apos; in Layer &apos;{self.ds.dataLyr.name()}&apos; oder Referenz-Linie &apos;{self.rs.snapped_ref_fid}&apos; in Layer &apos;{self.ds.refLyr.name()}&apos; ...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3262"/>
        <source>Update feature failed, missing privileges in layer &apos;{self.ds.dataLyr.name()}&apos;...</source>
        <translation>Speicherung fehlgeschlagen, fehlende Berechtigung in Layer &apos;{self.ds.dataLyr.name()}&apos;...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1360"/>
        <source>No valid reference-feature with fid &apos;{ref_fid}&apos;</source>
        <translation>Kein Linien-Feature mit FID &apos;{ref_fid}&apos;</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1375"/>
        <source>Feature with fid &apos;{ref_fid}&apos; without geometry</source>
        <translation>Datensatz FID &apos;{ref_fid}&apos; ohne Geometrie</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1377"/>
        <source>No Feature with fid &apos;{ref_fid}&apos; in reference-layer</source>
        <translation>Kein Datensatz mit FID &apos;{ref_fid}&apos; im Referenz-Layer</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1410"/>
        <source>Expression &apos;{dlg.expressionText()}&apos; valid and used as DisplayExpression for layer &apos;{self.ds.refLyr.name()}&apos;</source>
        <translation>Ausdruck &apos;{dlg.expressionText()}&apos; wird als DisplayExpression für Layer &apos;{self.ds.refLyr.name()}&apos; verwendet</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1412"/>
        <source>Expression &apos;{dlg.expressionText()}&apos; invalid and not used as DisplayExpression for layer &apos;{self.ds.refLyr.name()}&apos;, please check syntax!</source>
        <translation>Ausdruck &apos;{dlg.expressionText()}&apos; fehlerhaft, bitte Syntax prüfen!</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1415"/>
        <source>No reference-layer defined yet</source>
        <translation>Referenz-Layer noch nicht definiert</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1429"/>
        <source>Expression &apos;{dlg.expressionText()}&apos; valid and used as DisplayExpression for layer &apos;{self.ds.dataLyr.name()}&apos;</source>
        <translation>Ausdruck &apos;{dlg.expressionText()}&apos; wird als DisplayExpression für Layer &apos;{self.ds.dataLyr.name()}&apos; verwendet</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1431"/>
        <source>Expression &apos;{dlg.expressionText()}&apos; invalid and not used as DisplayExpression for layer &apos;{self.ds.dataLyr.name()}&apos;, please check syntax!</source>
        <translation>Ausdruck &apos;{dlg.expressionText()}&apos; fehlerhaft, bitte Syntax prüfen!</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1434"/>
        <source>No data-layer defined yet</source>
        <translation>Daten-Layer noch nicht definiert</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1448"/>
        <source>Expression &apos;{dlg.expressionText()}&apos; valid and used as DisplayExpression for layer &apos;{self.ds.showLyr.name()}&apos;</source>
        <translation>Ausdruck &apos;{dlg.expressionText()}&apos; wird als DisplayExpression für Layer &apos;{self.ds.showLyr.name()}&apos; verwendet</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1450"/>
        <source>Expression &apos;{dlg.expressionText()}&apos; invalid and not used as DisplayExpression for layer &apos;{self.ds.showLyr.name()}&apos;, please check syntax!</source>
        <translation>Ausdruck &apos;{dlg.expressionText()}&apos; fehlerhaft, bitte Syntax prüfen!</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1453"/>
        <source>No show-layer defined yet</source>
        <translation>Darstellungs-Layer noch nicht definiert</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1713"/>
        <source>Reference-Feature without Geometry (Reference-Layer &apos;{self.ds.refLyr.name()}&apos;, Field &apos;{self.ds.dataLyrReferenceField.name()}&apos;, Value &apos;{data_feature[self.ds.dataLyrReferenceField.name()]}&apos;)</source>
        <translation>Referenz-Datensatz-ohne Geometrie (Layer &apos;{self.ds.refLyr.name()}&apos;, Feld &apos;{self.ds.dataLyrReferenceField.name()}&apos;, ID &apos;{data_feature[self.ds.dataLyrReferenceField.name()]}&apos;)</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="2051"/>
        <source>Reference-layer &apos;{reference_layer.name()}&apos; is of type &apos;{wkb_label}&apos;, Line-on-Line-Features on multi-lines are not shown</source>
        <translation>Referenz-Layer &apos;{reference_layer.name()}&apos; hat Multi-Typ &apos;{wkb_label}&apos;, Point-on-Line-Features auf multi-Linien nicht darstellbar</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="2183"/>
        <source>Source-Format of chosen data-layer &apos;{data_layer.name()}&apos; is a file-based office-format (*.xlsx/*.odf), this not recommended...</source>
        <translation>Die Quelle des Layers  &apos;{data_layer.name()}&apos; ist ein dateibasiertes Office-Format (*.xlsx/*.odf), das ist nicht empfehlenswert...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="2198"/>
        <source>not allowed capabilities: {caps_string}
 â Some editing options will not be available</source>
        <translation>Fehlende Berechtigungen: {caps_string}
 ➜ Editiermöglichkeiten nur beschränkt verfügbar</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="2714"/>
        <source>Missing requirements: No show-layer configured...</source>
        <translation>Fehlende Voraussetzungen: Kein Darstellungs-Layer konfiguriert...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="2860"/>
        <source>LinearReferencing: Select or Create Geo-Package for Line-on-Line-Data</source>
        <translation>LinearReferencing: Geo-Package für Line-on-Line-Features auswählen oder anlegen</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="2900"/>
        <source>Name for Table in GeoPackage:</source>
        <translation>Tabellen-Name im GeoPackage:</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3126"/>
        <source>Canceled by user</source>
        <translation>Abbruch durch Anwender</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="2905"/>
        <source>Table &apos;{table_name}&apos; already exists in {gpkg_path} !

Replace existing Table?</source>
        <translation>Vorhandene Tabelle &apos;{table_name}&apos; in &apos;{gpkg_path}&apos; überschreiben?</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="2968"/>
        <source>create table &apos;{gpkg_path}&apos;.&apos;{table_name}&apos; successful</source>
        <translation>Tabelle &apos;{gpkg_path}&apos;.&apos;{table_name}&apos; wurde angelegt</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="2971"/>
        <source>Error creating data-layer &apos;{gpkg_path}&apos;.&apos;{table_name}&apos;, created layer not valid</source>
        <translation>Fehler beim Anlegen des Layers &apos;{gpkg_path}&apos;.&apos;{table_name}&apos;</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="2975"/>
        <source>Error creating data-layer &apos;{gpkg_path}&apos;.&apos;{table_name}&apos;: {writer.errorMessage()}</source>
        <translation>Fehler beim Anlegen des Layers &apos;{gpkg_path}&apos;.&apos;{table_name}&apos;: {writer.errorMessage()}</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3141"/>
        <source>missing requirements...</source>
        <translation>Fehlende Voraussetzungen...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="2996"/>
        <source>Name for Virtual Layer:</source>
        <translation>Name für den virtuellen Layer:</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3120"/>
        <source>Virtual layer created and added...</source>
        <translation>Virtueller Layer erzeugt und hinzugefügt...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3122"/>
        <source>Error creating virtual layer...</source>
        <translation>Fehler beim Anlegen des virtuellen Layers...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3128"/>
        <source>first create or configure reference- and data-layer</source>
        <translation>Bitte zuerst Referenz- und Datenlayer anlegen oder einrichten</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3167"/>
        <source>No completed measure yet...</source>
        <translation>Keine abgeschlossene Messung...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3225"/>
        <source>Delete feature with id &apos;{self.rs.edit_pk}&apos; from layer &apos;{self.ds.dataLyr.name()}&apos;?</source>
        <translation>Datensatz mit ID &apos;{self.rs.edit_pk}&apos; in Layer &apos;{self.ds.dataLyr.name()}&apos; löschen?</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3239"/>
        <source>Feature with ID &apos;{self.rs.edit_pk}&apos; successfully deleted in &apos;{self.ds.dataLyr.name()}&apos;...</source>
        <translation>Datensatz mit ID &apos;{self.rs.edit_pk}&apos; in Layer &apos;{self.ds.dataLyr.name()}&apos; gelöscht...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3259"/>
        <source>Delete feature failed, no feature &apos;{self.rs.edit_pk}&apos; in layer &apos;{self.ds.dataLyr.name()}&apos;...</source>
        <translation>Löschen des Datensatzes fehlgeschlagen, kein Datensatz mit ID &apos;{self.rs.edit_pk}&apos; in Layer &apos;{self.ds.dataLyr.name()}&apos; oder kein referenzierter-Datensatz &apos;{self.rs.snapped_ref_fid}&apos; in Layer &apos;{self.ds.refLyr.name()}&apos; ...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3324"/>
        <source>Feature with ID {self.rs.snapped_ref_fid} in Layer &apos;{self.ds.refLyr.name()}&apos; has no value in ID-field {self.ds.refLyrPkField.name()}</source>
        <translation>Datensatz mit FID {self.rs.snapped_ref_fid} in Layer &apos;{self.ds.refLyr.name()}&apos; ohne Referenz-Wert in Feld {self.ds.refLyrPkField.name()}</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3327"/>
        <source>No reference-feature with ID {self.rs.snapped_ref_fid} in Layer &apos;{self.ds.refLyr.name()}&apos;</source>
        <translation>Kein Referenz-Datensatz mit ID {self.rs.snapped_ref_fid} in Layer &apos;{self.ds.refLyr.name()}&apos;</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3370"/>
        <source>New feature with ID &apos;{used_pk}&apos; successfully added to &apos;{self.ds.dataLyr.name()}&apos;...</source>
        <translation>Datensatz mit ID &apos;{used_pk}&apos; in Layer &apos;{self.ds.dataLyr.name()}&apos; hinzugefügt...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3384"/>
        <source>Add feature failed, missing privileges in layer &apos;{self.ds.dataLyr.name()}&apos;...</source>
        <translation>Datensatz in Layer &apos;{self.ds.dataLyr.name()}&apos; konnte nicht angelegt werden, fehlende Privilegien...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3511"/>
        <source>tool_mode &apos;{tool_mode}&apos; not implemented...</source>
        <translation>tool_mode &apos;{tool_mode}&apos; nicht implementiert...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="4394"/>
        <source>Remove Feature from Selection</source>
        <translation>Datensatz aus Auswahl entfernen</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="4403"/>
        <source>Highlight Feature and Select for Edit</source>
        <translation>Datensatz hervorheben und zur Bearbeitung selektieren</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="4412"/>
        <source>Pan to Feature and Select for Edit</source>
        <translation>Auf Datensatz zoomen und zur Bearbeitung selektieren</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="4421"/>
        <source>Show Feature-Form</source>
        <translation>Datensatz-Formular öffnen</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="4450"/>
        <source>Highlight Reference-Feature</source>
        <translation>Linien-Shape hervorheben</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="4459"/>
        <source>Zoom to Reference-Feature</source>
        <translation>Auf Linien-Shape zoomen</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="4468"/>
        <source>Show Reference-Feature-Form</source>
        <translation>Referenz-Datensatz-Formular öffnen</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="4502"/>
        <source>Show Show-Feature-Form</source>
        <translation>Darstellungs-Layer-Formular öffnen</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="4564"/>
        <source>no feature with ID &apos;{edit_pk}&apos; in data-layer {self.ds.dataLyr.name()}</source>
        <translation>Kein Datensatz mit ID &apos;{edit_pk}&apos; in Layer {self.ds.dataLyr.name()}</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="4601"/>
        <source>no feature with value &apos;{edit_pk}&apos; in back-reference-field &apos;{self.ds.showLyrBackReferenceField.name()}&apos; of show-layer &apos;{self.ds.showLyr.name()}&apos;</source>
        <translation>Kein Datensatz mit Wert &apos;{edit_pk}&apos; im Rück-Referenz-Feld &apos;{self.ds.showLyrBackReferenceField.name()}&apos; des Layers &apos;{self.ds.showLyr.name()}&apos;</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="4652"/>
        <source>no feature with value &apos;{data_feature[self.ds.dataLyrReferenceField.name()]}&apos; in field &apos;{self.ds.dataLyrReferenceField.name()}&apos; of layer &apos;{self.ds.refLyr.name()}&apos;</source>
        <translation>Kein Datensatz mit Wert  &apos;{data_feature[self.ds.dataLyrReferenceField.name()]}&apos; im Feld &apos;{self.ds.dataLyrReferenceField.name()}&apos; des Layers &apos;{self.ds.refLyr.name()}&apos;</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="4627"/>
        <source>Reference-feature without geometry (Reference-Layer &apos;{self.ds.refLyr.name()}&apos;, field &apos;{self.ds.dataLyrReferenceField.name()}&apos;, value &apos;{data_feature[self.ds.dataLyrReferenceField.name()]}&apos;)</source>
        <translation>Referenz-Datensatz ohne Geometrie (Layer &apos;{self.ds.refLyr.name()}&apos;, Field &apos;{self.ds.dataLyrReferenceField.name()}&apos;, Wert &apos;{data_feature[self.ds.dataLyrReferenceField.name()]}&apos;)</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="4650"/>
        <source>Reference-feature without geometry (layer &apos;{self.ds.refLyr.name()}&apos;, field &apos;{self.ds.dataLyrReferenceField.name()}&apos;, value &apos;{data_feature[self.ds.dataLyrReferenceField.name()]}&apos;)</source>
        <translation>Referenz-Datensatz ohne Geometrie (Layer &apos;{self.ds.refLyr.name()}&apos;, Field &apos;{self.ds.dataLyrReferenceField.name()}&apos;, Wert &apos;{data_feature[self.ds.dataLyrReferenceField.name()]}&apos;)</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="460"/>
        <source>Initializing, please wait...</source>
        <translation>Initialisierung, bitte warten...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="462"/>
        <source>hover + left-mouse-down on map to snap reference-line and measure the from-point...</source>
        <translation>Referenzlinie auswählen und Startpunkt messen...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="463"/>
        <source>hold left mouse-button, drag to desired to-point, release mouse-button to measure the to-point...</source>
        <translation>Punkt mit gedrückter Maustaste verschieben, dort loslassen...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="464"/>
        <source>measure ended, see results in dialog, edit segment, add feature to data-layer or resume for next measure...</source>
        <translation>Messung beendet, Ergebnisse im Dialog editeren und/oder speichern, Klick auf Karte für neue Messung...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="466"/>
        <source>mouse-down on canvas and move from-point to the desired location on reference-line...</source>
        <translation>Startpunkt auf Referenzlinie verschieben...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="467"/>
        <source>mouse-release to position from-point on snapped reference-line...</source>
        <translation>Maustaste an Zielposition der Referenzlinie loslassen...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="469"/>
        <source>mouse-down on canvas and move to-point to the desired location on reference-line......</source>
        <translation>Endpunkt auf Referenzlinie verschieben...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="470"/>
        <source>mouse-release to position to-point on snapped reference-line...</source>
        <translation>Maustaste an Zielposition der Referenzlinie loslassen...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="472"/>
        <source>click the segment and start dragging, supports [ctrl] or [shift] modifiers...</source>
        <translation>Segment auf Karte anklicken und verschieben, [ctrl] oder [Shift]-Varianten...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="473"/>
        <source>drag and release the selected segment, supports [ctrl] or [shift] modifiers...</source>
        <translation>Segment auf Karte verschieben, Maustaste loslassen , [ctrl] oder [Shift]-Varianten...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="475"/>
        <source>no reference-layer (linestring) found or configured, check settings...</source>
        <translation>Kein Referenzlayer konfiguriert...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="477"/>
        <source>click or draw rect to select features for edit</source>
        <translation>gewünschte Elemente anklicken oder mit Rechteck selektieren</translation>
    </message>
</context>
<context>
    <name>mt</name>
    <message>
        <location filename="../map_tools/FeatureActions.py" line="155"/>
        <source>no valid feature for FID {fid} in Layer &apos;{layer_id}&apos;...</source>
        <translation>kein valider Datensatz mit FID {fid} in Layer &apos;{layer_id}&apos;...</translation>
    </message>
    <message>
        <location filename="../map_tools/FeatureActions.py" line="157"/>
        <source>Missing configuration Show-layer-&gt;Back-Reference-Field...</source>
        <translation>Fehlende Konfiguration: Darstellungs-Layer➜Rück-Referenz-Feld...</translation>
    </message>
    <message>
        <location filename="../map_tools/FeatureActions.py" line="161"/>
        <source>layer &apos;{data_or_show_lyr}&apos; not registered as data-layer or show-layer, please redefine layers in plugin-dialogue!</source>
        <translation>Layer &apos;{data_or_show_lyr}&apos; nicht als Daten- oder Darstellungslayer konfiguriert!</translation>
    </message>
</context>
</TS>
