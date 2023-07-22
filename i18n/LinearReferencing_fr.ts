<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="fr_FR" sourcelanguage="en_US">
<context>
    <name>CheckFlags</name>
    <message>
        <location filename="../map_tools/PolEvt.py" line="695"/>
        <source>please select an entry from the list above...</source>
        <translation>Veuillez sélectionner un élément dans la liste ci-dessus...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="642"/>
        <source>Configuration &apos;{setting_label}&apos; restored...</source>
        <translation>Configuration &apos;{setting_label}&apos; restaurée...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="706"/>
        <source>Delete Configuration &apos;{setting_label}&apos;?</source>
        <translation>Supprimer la configuration &apos;{setting_label}&apos;&#xa0;?</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="719"/>
        <source>Configuration &apos;{setting_label}&apos; deleted...</source>
        <translation>Configuration &apos;{setting_label}&apos; supprimée...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2903"/>
        <source>Canceled by user...</source>
        <translation>Annulé par l&apos;utilisateur...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2568"/>
        <source>LinearReferencing ({gdp()})</source>
        <translation>LinearReferencing ({gdp()})</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="745"/>
        <source>Label for Configuration:</source>
        <translation>Nom pour la configuration:</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="758"/>
        <source>Replace stored Configuration &apos;{new_label}&apos;?</source>
        <translation>Remplacer la configuration stockée &apos;{new_label}&apos;&#xa0;?</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="783"/>
        <source>number of stored settings exceeds maximum ({self._num_storable_settings}), please replace existing one...</source>
        <translation>Le nombre de paramètres enregistrés dépasse le maximum ({self._num_storable_settings}), veuillez en remplacer un existant...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="799"/>
        <source>Current configuration stored under &apos;{new_label}&apos;...</source>
        <translation>Configuration actuelle stockée sous &apos;{new_label}&apos;...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1014"/>
        <source>No valid reference-feature with fid &apos;{ref_fid}&apos;</source>
        <translation>Aucune référence feature valide avec FID &apos;{ref_fid}&apos;</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1091"/>
        <source>no reference-feature with ID &apos;{data_feature[self.ds.dataLyrReferenceField.name()]}&apos; in layer {self.ds.refLyr.name()}</source>
        <translation>Aucune référence feature avec FID &apos;{ref_fid}&apos;</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1094"/>
        <source>no feature with ID &apos;{edit_pk}&apos; in layer {self.ds.dataLyr.name()}</source>
        <translation>Aucune feature avec ID &apos;{edit_pk}&apos; dans la couche {self.ds.dataLyr.name()}</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1246"/>
        <source>Missing requirements, reference-, data- and show-layer required...</source>
        <translation>Exigences manquantes, couche de référence, de données et d&apos;affichage nécessaire...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1158"/>
        <source>No selection in data-layer...</source>
        <translation>Aucune sélection dans la couche de données...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1226"/>
        <source>no extent calculable for these features</source>
        <translation>aucune étendue calculable pour ces enregistrements</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1244"/>
        <source>No selection in show-layer...</source>
        <translation>Aucune sélection dans la couche de préséntation...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2758"/>
        <source>Referenced Linestring-Geometry &apos;{self.rs.snapped_ref_fid}&apos; in Layer &apos;{self.ds.refLyr.name()}&apos; is multi-part ({ref_feature.geometry().constGet().partCount()} parts), measured Point-on-Line-Feature may be invisible in Show-Layer</source>
        <translation>La géométrie de la chaîne de lignes référencée &apos;{self.rs.snapped_ref_fid}&apos; dans la couche &apos;{self.ds.refLyr.name()}&apos; est en plusieurs parties ({ref_feature.geometry().constGet().partCount()} parties) , L&apos;entité point sur ligne mesurée peut être invisible dans la couche de préséntation</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1311"/>
        <source>Feature with ID &apos;{self.rs.edit_pk}&apos; successfully updated in &apos;{self.ds.dataLyr.name()}&apos;...</source>
        <translation>Enregistrement mis à jour avec l&apos;ID &apos;{self.rs.edit_pk}&apos;...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1317"/>
        <source>Update feature failed, measure out of range 0 ... {update_ref_feature.geometry().length()}</source>
        <translation>L&apos;enregistrement de l&apos;ensemble de données a échoué, stationnant en dehors de la plage de valeurs 0 ... {update_ref_feature.geometry().length()}</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1320"/>
        <source>Update feature failed, no reference-feature with PK &apos;{updare_ref_pk}&apos; in layer &apos;{self.ds.refLyr.name()}&apos; ...</source>
        <translation>Échec de la sauvegarde, aucune ligne de référence avec l&apos;ID &apos;{updare_ref_pk}&apos; dans la couche &apos;{self.ds.refLyr.name()}&apos; ...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1329"/>
        <source>Update feature failed, no feature &apos;{self.rs.edit_pk}&apos; in layer &apos;{self.ds.dataLyr.name()}&apos; or reference-feature &apos;{self.rs.snapped_ref_fid}&apos; in layer &apos;{self.ds.refLyr.name()}&apos; ...</source>
        <translation>Échec de la sauvegarde de l&apos;enregistrement, pas d&apos;entité &apos;{self.rs.edit_pk}&apos; dans la couche &apos;{self.ds.dataLyr.name()}&apos; ou d&apos;entité de référence &apos;{self.rs.snapped_ref_fid}&apos; dans la couche &apos;{self.ds .refLyr.nom()}&apos; ...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1331"/>
        <source>Update feature failed, missing privileges in layer &apos;{self.ds.dataLyr.name()}&apos;...</source>
        <translation>Échec de l&apos;enregistrement, manque d&apos;autorisation sur la couche &apos;{self.ds.dataLyr.name()}&apos;...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1394"/>
        <source>Expression &apos;{dlg.expressionText()}&apos; valid and used as DisplayExpression for layer &apos;{self.ds.refLyr.name()}&apos;</source>
        <translation>L&apos;expression &apos;{dlg.expressionText()}&apos; est utilisée comme DisplayExpression pour la couche &apos;{self.ds.refLyr.name()}&apos;</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1396"/>
        <source>Expression &apos;{dlg.expressionText()}&apos; invalid and not used as DisplayExpression for layer &apos;{self.ds.refLyr.name()}&apos;, please check syntax!</source>
        <translation>Expression &apos;{dlg.expressionText()}&apos; incorrecte, veuillez vérifier la syntaxe!</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1399"/>
        <source>No reference-layer defined yet</source>
        <translation>Couche de référence pas encore définie</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1413"/>
        <source>Expression &apos;{dlg.expressionText()}&apos; valid and used as DisplayExpression for layer &apos;{self.ds.dataLyr.name()}&apos;</source>
        <translation>L&apos;expression &apos;{dlg.expressionText()}&apos; est utilisée comme DisplayExpression pour la couche &apos;{self.ds.dataLyr.name()}&apos;</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1415"/>
        <source>Expression &apos;{dlg.expressionText()}&apos; invalid and not used as DisplayExpression for layer &apos;{self.ds.dataLyr.name()}&apos;, please check syntax!</source>
        <translation>Expression &apos;{dlg.expressionText()}&apos; incorrecte, veuillez vérifier la syntaxe!</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1418"/>
        <source>No data-layer defined yet</source>
        <translation>Couche pour data pas encore définie</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1432"/>
        <source>Expression &apos;{dlg.expressionText()}&apos; valid and used as DisplayExpression for layer &apos;{self.ds.showLyr.name()}&apos;</source>
        <translation>L&apos;expression &apos;{dlg.expressionText()}&apos; est utilisée comme DisplayExpression pour la couche &apos;{self.ds.showLyr.name()}&apos;</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1434"/>
        <source>Expression &apos;{dlg.expressionText()}&apos; invalid and not used as DisplayExpression for layer &apos;{self.ds.showLyr.name()}&apos;, please check syntax!</source>
        <translation>Expression &apos;{dlg.expressionText()}&apos; incorrecte, veuillez vérifier la syntaxe!</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1437"/>
        <source>No show-layer defined yet</source>
        <translation>Couche pour dessin pas encore défini</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1728"/>
        <source>Reference-layer &apos;{reference_layer.name()}&apos; is of type &apos;{wkb_label}&apos;, Point-on-Line-Features on multi-lines are not shown</source>
        <translation>La couche de référence &apos;{reference_layer.name()}&apos; a le type de géométrie &apos;{wkb_label}&apos;, les entités ponctuelles sur plusieurs lignes ne sont pas dessinées</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1930"/>
        <source>Source-Format of chosen data-layer &apos;{data_layer.name()}&apos; is a file-based office-format (*.xlsx/*.odf), this not recommended...</source>
        <translation>La source de la couche &apos;{data_layer.name()}&apos; est un format bureautique basé sur un fichier (*.xlsx/*.odf), ce n&apos;est pas recommandé...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2343"/>
        <source>Missing requirements: No show-layer configured...</source>
        <translation>Conditions préalables manquantes: aucune couche de préséntation définie...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2444"/>
        <source>LinearReferencing: Create Point-on-Line-Data-Layer</source>
        <translation>LinearReferencing&#xa0;: créer des couches de données point-sur-ligne</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2475"/>
        <source>Name for Table in GeoPackage:</source>
        <translation>Nom de la table dans GeoPackage:</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2677"/>
        <source>Canceled by user</source>
        <translation>Annulé par l&apos;utilisateur</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2538"/>
        <source>create table &apos;{gpkg_path}&apos;.&apos;{table_name}&apos; successful</source>
        <translation>La table &apos;{gpkg_path}&apos;.&apos;{table_name}&apos; a été créée</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2542"/>
        <source>Error creating data-layer &apos;{gpkg_path}&apos;.&apos;{table_name}&apos;, created layer not valid</source>
        <translation>Erreur lors de la création de la couche &apos;{gpkg_path}&apos;.&apos;{table_name}&apos;</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2546"/>
        <source>Error creating data-layer &apos;{gpkg_path}&apos;.&apos;{table_name}&apos;: {writer.errorMessage()}</source>
        <translation>Erreur lors de la création de la couche &apos;{gpkg_path}&apos;.&apos;{table_name}&apos;: {writer.errorMessage()}</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2548"/>
        <source>missing requirements...</source>
        <translation>Conditions préalables manquantes...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2568"/>
        <source>Name for Virtual Layer:</source>
        <translation>Nom de la couche virtuelle:</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2672"/>
        <source>Virtual layer created and added...</source>
        <translation>Couche virtuelle créée et ajoutée...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2675"/>
        <source>Error creating virtual layer...</source>
        <translation>Erreur lors de la création de la couche virtuelle...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2679"/>
        <source>first create or configure reference- and data-layer</source>
        <translation>Veuillez d&apos;abord créer ou configurer des couches de référence et de données</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2754"/>
        <source>Feature with ID {self.rs.snapped_ref_fid} in Layer &apos;{self.ds.refLyr.name()}&apos; has no value in ID-field {self.ds.refLyrPkField.name()}</source>
        <translation>Enregistrer avec le FID {self.rs.snapped_ref_fid} dans la couche &apos;{self.ds.refLyr.name()}&apos; sans valeur de référence dans le champ {self.ds.refLyrPkField.name()}</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2760"/>
        <source>No reference-feature with ID {self.rs.snapped_ref_fid} in layer &apos;{self.ds.refLyr.name()}&apos;</source>
        <translation>Aucun enregistrement avec l&apos;ID {self.rs.snapped_ref_fid} dans la couche &apos;{self.ds.refLyr.name()}&apos;</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2811"/>
        <source>New feature with ID &apos;{used_pk}&apos; successfully added to &apos;{self.ds.dataLyr.name()}&apos;...</source>
        <translation>Ensemble de données ajouté avec l&apos;ID &apos;{used_pk}&apos; dans la couche &apos;{self.ds.dataLyr.name()}&apos;...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2824"/>
        <source>Add feature failed, missing privileges in layer &apos;{self.ds.dataLyr.name()}&apos;...</source>
        <translation>L&apos;ensemble de données dans la couche &apos;{self.ds.dataLyr.name()}&apos; n&apos;a pas pu être créé, privilèges manquants...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2876"/>
        <source>Delete Feature with id &apos;{self.rs.edit_pk}&apos; from layer &apos;{self.ds.dataLyr.name()}&apos;?</source>
        <translation>Supprimer l&apos;enregistrement avec l&apos;ID &apos;{self.rs.edit_pk}&apos; dans la couche &apos;{self.ds.dataLyr.name()}&apos;?</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2890"/>
        <source>Feature with ID &apos;{self.rs.edit_pk}&apos; successfully deleted in &apos;{self.ds.dataLyr.name()}&apos;...</source>
        <translation>Enregistrement avec l&apos;ID &apos;{self.rs.edit_pk}&apos; dans la couche &apos;{self.ds.dataLyr.name()}&apos; supprimé...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2906"/>
        <source>Delete feature failed, no feature &apos;{self.rs.edit_pk}&apos; in layer &apos;{self.ds.dataLyr.name()}&apos;...</source>
        <translation>Échec de la suppression de l&apos;enregistrement, aucun enregistrement avec l&apos;ID &apos;{self.rs.edit_pk}&apos; dans la couche &apos;{self.ds.dataLyr.name()}&apos; ou aucun enregistrement référencé &apos;{self.rs.snapped_ref_fid}&apos; dans la couche &apos; {self.ds.refLyr.name()}&apos; ...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2909"/>
        <source>Delete feature failed, missing privileges in layer &apos;{self.ds.dataLyr.name()}&apos;...</source>
        <translation>Impossible de supprimer l&apos;ensemble de données dans la couche &apos;{self.ds.dataLyr.name()}&apos;, privilèges manquants...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2912"/>
        <source>Delete feature failed, no feature selected...</source>
        <translation>Échec de la suppression, aucun enregistrement sélectionné...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="3004"/>
        <source>tool_mode &apos;{tool_mode}&apos; not implemented...</source>
        <translation>tool_mode &apos;{tool_mode}&apos; non implémenté...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="3748"/>
        <source>Remove Feature from Selection</source>
        <translation>Supprimer l&apos;enregistrement de la sélection</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="3757"/>
        <source>Highlight Feature and Select for Edit</source>
        <translation>Mettez en surbrillance l&apos;enregistrement et sélectionnez-le pour le modifier</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="3766"/>
        <source>Pan to Feature and Select for Edit</source>
        <translation>Zoomer sur le jeu de données et sélectionner pour l&apos;édition</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="3775"/>
        <source>Show Feature-Form</source>
        <translation>Ouvrir le formulaire d&apos;enregistrement</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="3802"/>
        <source>Highlight Reference-Feature</source>
        <translation>Mettre en surbrillance la forme de la ligne</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="3811"/>
        <source>Zoom to Reference-Feature</source>
        <translation>Zoom sur la forme de la ligne</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="3820"/>
        <source>Show Reference-Feature-Form</source>
        <translation>Ouvrir la couche de référence du formulaire d&apos;ensemble de données</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="3847"/>
        <source>Show Show-Feature-Form</source>
        <translation>Ouvrir la couche de préséntation du formulaire de jeu de données</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="3919"/>
        <source>no feature with ID &apos;{edit_pk}&apos; in data-layer {self.ds.dataLyr.name()}</source>
        <translation>Aucun enregistrement avec l&apos;ID &apos;{edit_pk}&apos; dans la couche {self.ds.dataLyr.name()}</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="3957"/>
        <source>no feature with value &apos;{edit_pk}&apos; in back-reference-field &apos;{self.ds.showLyrBackReferenceField.name()}&apos; of show-layer &apos;{self.ds.showLyr.name()}&apos;</source>
        <translation>Aucun enregistrement avec la valeur &apos;{edit_pk}&apos; dans le champ de référence arrière &apos;{self.ds.showLyrBackReferenceField.name()}&apos; de la couche &apos;{self.ds.showLyr.name()}&apos;</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="4003"/>
        <source>no feature with value &apos;{data_feature[self.ds.dataLyrReferenceField.name()]}&apos; in field &apos;{self.ds.dataLyrReferenceField.name()}&apos; of layer &apos;{self.ds.refLyr.name()}&apos;</source>
        <translation>Aucun enregistrement avec la valeur &apos;{data_feature[self.ds.dataLyrReferenceField.name()]}&apos; dans le champ &apos;{self.ds.dataLyrReferenceField.name()}&apos; de la couche &apos;{self.ds.refLyr.name()}&apos;</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="4001"/>
        <source>Reference-feature without geometry (layer &apos;{self.ds.refLyr.name()}&apos;, field &apos;{self.ds.dataLyrReferenceField.name()}&apos;, value &apos;{data_feature[self.ds.dataLyrReferenceField.name()]}&apos;)</source>
        <translation>Jeu de données de référence sans géométrie (couche &apos;{self.ds.refLyr.name()}&apos;, champ &apos;{self.ds.dataLyrReferenceField.name()}&apos;, valeur &apos;{data_feature[self.ds.dataLyrReferenceField.name()]]}&apos;)</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1360"/>
        <source>Feature with FID &apos;{ref_fid}&apos; in reference-layer &apos;{self.ds.refLyr.name()}&apos; not found or not valid</source>
        <translation>Aucune enregistrement valide avec FID &apos;{ref_fid}&apos; dans la couche &apos;{self.ds.refLyr.name()}&apos;</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1546"/>
        <source>Feature with fid &apos;{ref_fid}&apos; not found, not valid or without geometry</source>
        <translation>Aucune enregistrement valide avec FID &apos;{ref_fid}&apos;</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="385"/>
        <source>Initializing, please wait...</source>
        <translation>Initialisation, veuillez patienter...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="387"/>
        <source>hover and click on reference-line to show coords and measures...</source>
        <translation>Déplacez le curseur sur la ligne de référence, cliquez pour mesurer...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="388"/>
        <source>Point on reference-line measured, edit, add feature or click again to resume...</source>
        <translation></translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="389"/>
        <source>grab point on canvas and move it to desired position on selected line</source>
        <translation></translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="390"/>
        <source>hold mouse-button, move grabbed point to desired position and release</source>
        <translation></translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="392"/>
        <source>no reference-layer (linestring) found or configured...</source>
        <translation></translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="393"/>
        <source>click or draw rect to select features [ctrl] â remove from Feature-Selection [shift] â add to Feature-Selection [-] â replace Feature-Selection</source>
        <translation>Sélectionner des entités (point/rectangle) [ctrl] ➜ supprimer de la liste de sélection [shift] ➜ ajouter [-] ➜ remplacer</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="394"/>
        <source>hover and click on reference-line to reposition selected feature, click &apos;update&apos; to save feature...</source>
        <translation>Repositionner et enregistrer l&apos;entité sélectionnée...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="395"/>
        <source>selected feature repositioned, click &apos;update&apos; to save...</source>
        <translation>élément sélectionné repositionné, enregistrer maintenant...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="591"/>
        <source>No completed measure yet...</source>
        <translation>Aucune mesure terminée...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2855"/>
        <source>Layer &apos;{self.ds.dataLyr.name()}&apos; is editable!

[Yes]        â End edit session with save
[No]         â End edit session without save 
[Cancel]  â Quit...</source>
        <translation>La couche &apos;{self.ds.dataLyr.name()}&apos; est modifiable&#xa0;!

[Oui] ➜ Enregistrer les modifications et continuer
[Non] ➜ Refuser les modifications et continuer
[Annuler] ➜ Abandonner...</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="1945"/>
        <source>not allowed capabilities: {caps_string}
 ➜ Some editing options will not be available</source>
        <translation>Privilèges manquants&#xa0;: {caps_string}
  ➜ Certaines options d&apos;édition ne seront pas disponibles</translation>
    </message>
    <message>
        <location filename="../map_tools/PolEvt.py" line="2481"/>
        <source>Table &apos;{table_name}&apos; already exists in {gpkg_path} !

Replace?</source>
        <translation>La table &apos;{table_name}&apos; existe déjà dans &apos;{gpkg_path}&apos;&#xa0;!

Remplaçant?</translation>
    </message>
</context>
<context>
    <name>LinearReference</name>
    <message>
        <location filename="../LinearReference.py" line="149"/>
        <source>&lt;b&gt;LinearReferencing&lt;/b&gt;&lt;hr&gt;Measure and Digitize Point-on-Line Features</source>
        <translation>&amp;lt;b&amp;gt;LinearReferencing&amp;lt;/b&amp;gt;&amp;lt;hr&amp;gt;Mesurer et numériser les entités ponctuelles en ligne</translation>
    </message>
    <message>
        <location filename="../LinearReference.py" line="159"/>
        <source>&lt;b&gt;LinearReferencing&lt;/b&gt;&lt;hr&gt;Measure and Digitize Line-on-Line Features</source>
        <translation>&amp;lt;b&amp;gt;LinearReferencing&amp;lt;/b&amp;gt;&amp;lt;hr&amp;gt;Mesurer et numériser les entités ligne en ligne</translation>
    </message>
    <message>
        <location filename="../LinearReference.py" line="169"/>
        <source>&lt;b&gt;LinearReferencing&lt;/b&gt;&lt;hr&gt;Show Help</source>
        <translation>&amp;lt;b&amp;gt;LinearReferencing&amp;lt;/b&amp;gt;&amp;lt;hr&amp;gt;Obtenir de l&apos;aide</translation>
    </message>
</context>
<context>
    <name>LolDialog</name>
    <message>
        <location filename="../dialogs/LolDialog.py" line="58"/>
        <source>Linear Referencing: Line-on-Line</source>
        <translation>Linear Referencing: ligne en ligne</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="107"/>
        <source>toggle window dockable/undockable</source>
        <translation>Ancrer/détacher la fenêtre</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="119"/>
        <source>Measure:</source>
        <translation>Mesure:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="848"/>
        <source>Reference-Line:</source>
        <translation>Ligne de référence:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="151"/>
        <source>Open Form</source>
        <translation>Formulaire ouvert</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="160"/>
        <source>Zoom to Feature</source>
        <translation>Zoom sur l&apos;ensemble de données</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="165"/>
        <source>Offset:</source>
        <translation>Offset:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="190"/>
        <source>From:</source>
        <translation>Départ:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="191"/>
        <source>To:</source>
        <translation>Fin:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="206"/>
        <source>Snapped Point x/y:</source>
        <translation>Snapped-Point x/y:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="224"/>
        <source>Measure (abs / fract):</source>
        <translation>Mesure (abs/fract):</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="233"/>
        <source>Measure-From as percentage
 - range 0...100</source>
        <translation>Pourcentage du point de départ du stationnement
  - Plage de valeurs 0...100</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="245"/>
        <source>Measure-To as percentage
 - range 0...100</source>
        <translation>Pourcentage du point final du stationnement
  - Plage de valeurs 0...100</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="255"/>
        <source>Distance</source>
        <translation>Section</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="264"/>
        <source>moves segment to reference-line-start-point</source>
        <translation>Déplacer la segment au point de départ de la ligne de référence</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="271"/>
        <source>&apos;prepend&apos; segment (new to-measure == old from-measure)</source>
        <translation>Déplacer la section vers le point de départ (nouvel emplacement de fin == ancien emplacement de départ)</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="286"/>
        <source>enlarge/shrink segment
   - keeps From-Point, moves To-Point
   - units accordingly Layer-Projection
   - ctrl/shift/ctrl+shift spinbutton-click-modifiers with factors 10/100/1000</source>
        <translation>Diminuer/augmenter le segment
      Le point de départ est conservé, le point final est décalé
      Unités correspondant à la projection de la couche
      ctrl/shift/ctrl+shift Cliquer sur les boutons spin ➜ Facteur 10/100/1000</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="303"/>
        <source>&apos;append&apos; segment (new from-measure == old to-measure)</source>
        <translation>Déplacer la section vers le point final (nouvel emplacement de départ == ancien emplacement de fin)</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="310"/>
        <source>move segment to reference-line-end-point</source>
        <translation>Déplacer la section au point final de la ligne de référence</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="319"/>
        <source>zoom to segment</source>
        <translation>zoomer sur la segment</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="331"/>
        <source>move From-Point</source>
        <translation>Déplacer le point de départ</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="335"/>
        <source>move From-Point by mouse-down and drag on selected reference-line</source>
        <translation>Déplacer le point de départ</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="339"/>
        <source>move To-Point</source>
        <translation>Déplacer le point final</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="343"/>
        <source>move To-Point by mouse-down and drag on selected reference-line</source>
        <translation>Déplacer le point final sur la carte</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="350"/>
        <source>Move segment</source>
        <translation>Déplacer segment</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="354"/>
        <source>Move segment interactive:
   [-]	-&gt; change measure, keep offset
 [shift]	-&gt; change offset, keep measure
  [ctrl]	-&gt; change offset and measure</source>
        <translation>Déplacer la section sur la carte :
   [ - ]	➜ stationnement
   [shiftl]	➜ distance
   [ctrl]	➜ distance et stationnement</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="361"/>
        <source>Resume measure</source>
        <translation>Mesure sommaire</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="364"/>
        <source>Reset results and start new measure</source>
        <translation>Réinitialiser les résultats, nouvelle mesure</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="372"/>
        <source>Edit:</source>
        <translation>Modifier:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="380"/>
        <source>Selected PK:</source>
        <translation>Enregistrement sélectionné:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="390"/>
        <source>Update</source>
        <translation>Enregistrer</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="393"/>
        <source>Update selected feature...</source>
        <translation>enregistrer le jeu de données sélectionné...</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="398"/>
        <source>Insert</source>
        <translation>Ajouter</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="401"/>
        <source>Insert feature / duplicate selected feature...</source>
        <translation>Ajouter ou dupliquer enregistrement...</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="406"/>
        <source>Delete</source>
        <translation>Supprimer</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="409"/>
        <source>Delete selected feature...</source>
        <translation>supprimer l&apos;enregistrement de données sélectionné...</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="416"/>
        <source>Feature-Selection:</source>
        <translation>Sélection pour l&apos;édition:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="431"/>
        <source>Select Feature(s)</source>
        <translation>Sélectionner des enregistrements</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="434"/>
        <source>Select Features from Show-Layer
    click (point) or drag (rectangle)
    [Shift] â append
    [Ctrl] â remove</source>
        <translation>Sélectionnez afficher les enregistrements de calque
     Point (simple) ou rectangle (sélection multiple)
     [Maj] ➜ Ajouter des enregistrements
     [Ctrl] ➜ Supprimer les enregistrements</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="439"/>
        <source>Insert all Features</source>
        <translation>Ajouter tous les enregistrements de la couche de données</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="442"/>
        <source>Insert all Features from Data-Layer
    [Shift] â append</source>
        <translation>Ajouter tous les enregistrements de la couche de données
     [Maj] ➜ Développer la sélection</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="447"/>
        <source>Insert selected Data-Layer-Features</source>
        <translation>Ajouter sélection de couche de données</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="450"/>
        <source>Insert selected Features from Data-Layer
    [Shift] â append</source>
        <translation>Ajouter les entités sélectionnées de la couche de données
     [Maj] ➜ Développer la sélection</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="455"/>
        <source>Insert selected Show-Layer-Features</source>
        <translation>Ajouter les entités sélectionnées de la couche de préséntation</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="458"/>
        <source>Insert selected Features from Show-Layer
    [Shift] â append</source>
        <translation>Ajouter les entités sélectionnées de la couche de préséntation
     [Maj] ➜ Développer la sélection</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="492"/>
        <source>Zoom to feature-selection</source>
        <translation>Zoom sur la sélection</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="495"/>
        <source>Zoom to selected features</source>
        <translation>Zoom sur la sélection</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="499"/>
        <source>Clear Feature-Selection</source>
        <translation>Réinitialiser la sélection</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="514"/>
        <source>Layers and Fields:</source>
        <translation>Couches et colonnes:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="520"/>
        <source>Reference-Layer...</source>
        <translation>Couche de référence...</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="534"/>
        <source>Reference-layer, provides linestring-geometries
  geometry-Type linestring/m/z
  multi-linestring/m/z</source>
        <translation>Couche de référence, renvoie les géométries de lignes, le type de géométrie
    ligne/m/z
    chaîne multiligne/m/z</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="729"/>
        <source>Open Table</source>
        <translation>ouverte table</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="738"/>
        <source>Edit Display-Expression for this Layer</source>
        <translation>Modifier l&apos;expression de préséntation de ce couche</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="616"/>
        <source>      ... ID-Field:</source>
        <translation>      ... Colonne pour ID:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="570"/>
        <source>Identifier-Field, used for assignment to Data-Layer
   type integer or string, unique, not null
   typically the PK-Field</source>
        <translation>Colonne de référence à la couche de données
    integer ou string, unique, non nul
    généralement PK-colonne</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="574"/>
        <source>Data-Layer...</source>
        <translation>Couche de données...</translation>
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
        <translation>Couche d&apos;entités ligne sur ligne:
    sans géométrie
    modifiable
Colonnes obligatoires&#xa0;:
    ID (PK)
    Référence à la couche de ligne
    début de mesure
    fin de mesure
    Distance</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="742"/>
        <source>...or create</source>
        <translation>...ou créer</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="612"/>
        <source>Create a non-geometry GPKG-Layer for storing measure-data</source>
        <translation>Créer une couche GPKG sans géométrie pour les entités ligne sur ligne</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="630"/>
        <source>Field with unique key,
   type integer or string
   typically the PK-Field</source>
        <translation>ID-Colonne
    unique, non nul
    integer ou string
    généralement la colonne PK</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="634"/>
        <source>      ... Reference-Field:</source>
        <translation>      ... Colonne de référence:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="648"/>
        <source>Field for assignment to Reference-Layer
   type matching to Reference-Layer-ID-Field</source>
        <translation>Colonne de mappage à la couche de référence
    type approprié</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="652"/>
        <source>      ... Measure-From-Field:</source>
        <translation>      ... Colonne pour début de mesure:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="666"/>
        <source>Field for storing measure-from
   distance of segment-start to startpoint of assigned line
   numeric type</source>
        <translation>Colonne pour début de mesure
   Distance au point de départ de l&apos;entité linéaire associée
   type numérique</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="670"/>
        <source>      ... Measure-To-Field:</source>
        <translation>      ... Colonne pour fin de mesure:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="684"/>
        <source>Field for storing measure-to
   distance of segment-end to startpoint of assigned line
   numeric type</source>
        <translation>Colonne pour fin de mesure
   Distance au point de départ de l&apos;entité linéaire associée
   type numérique</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="688"/>
        <source>      ... Offset-Field:</source>
        <translation>      ... Colonne Distance:</translation>
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
        <translation>Colonne pour la distance à la ligne de référence assignée
    type numérique
    &amp;gt; 0 ➜ gauche
    &amp;lt; 0 ➜ droite
   = 0 ➜ sur la ligne de référence</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="706"/>
        <source>Show-Layer...</source>
        <translation>Couche de présentation...</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="720"/>
        <source>Layer to show the Line-on-Line-Features
Source-Type:
     virtual (with query to Reference- and  Data-Layer)
     ogr (f.e. view in PostGIS or GPKG)</source>
        <translation>Couche représentant les entités ligne sur ligne:
      couche QGis virtuelle avec requête de couche de référence et de données
      ogr (par exemple vue PostGIS ou GPKG)</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="744"/>
        <source>Create a virtual Layer for showing the results</source>
        <translation>créer une couche virtuelle pour reprentation</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="748"/>
        <source>      ... Back-Reference-Field:</source>
        <translation>      ... colonne de référence arrière:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="762"/>
        <source>Field for Back-Reference to data-layer
   Field-Type and Contents matching to Data-Layer-ID-Field
   typically the PK-Fields in both layers</source>
        <translation>Colonne avec référence arrière à la couche de données
    Type et contenu correspondant au colonne ID de la couche de données
    généralement le PK-colonne dans les deux couches</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="769"/>
        <source>Styles:</source>
        <translation>Modes:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="784"/>
        <source>Symbol</source>
        <translation>Symbole</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="785"/>
        <source>Size</source>
        <translation>Taille</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="786"/>
        <source>Width</source>
        <translation>Large</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="787"/>
        <source>Color</source>
        <translation>Couleur</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="788"/>
        <source>Fill-Color</source>
        <translation>Couleur de remplissage</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="792"/>
        <source>From-Point:</source>
        <translation>Point de départ:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="813"/>
        <source>To-Point:</source>
        <translation>Point final:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="834"/>
        <source>Segment-Line:</source>
        <translation>Segment-Ligne:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="863"/>
        <source>Store/Restore Configurations:</source>
        <translation>Enregistrer/restaurer les configurations:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="870"/>
        <source>Stored Configurations:</source>
        <translation>Configurations enregistrés:</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="895"/>
        <source>Measure</source>
        <translation>Mesure</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="897"/>
        <source>Settings</source>
        <translation>Configuration</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="878"/>
        <source>Store current configuration...</source>
        <translation>Enregistrer les paramètres actuels...</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="881"/>
        <source>Restore selected configuration...</source>
        <translation>restaurer la configuration sélectionnée...</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="884"/>
        <source>Delete selected configuration...</source>
        <translation>supprimer la configuration sélectionnée...</translation>
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
        <translation>Distance entre le segment et la ligne de référence
    &amp;gt; 0 restant
    &amp;lt; 0 droite
    ctrl/shift/ctrl+shift Cliquez sur les boutons ➜ facteur 10/100/1000</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="228"/>
        <source>Measure From-Point
 - range 0...length_of_line
 - units accordingly Layer-Projection
 - ctrl/shift/ctrl+shift click-modifiers with factors 10/100/1000</source>
        <translation>Stationnement du point de départ
  - Plage de valeurs 0...longueur de ligne
  - Unité de mesure comme projection de couche
  - ctrl/shift/ctrl+shift clic-➜ facteur 10/100/1000</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="240"/>
        <source>Measure To-Point
 - range 0...length_of_line
 - units accordingly Layer-Projection
 - ctrl/shift/ctrl+shift spinbutton-click-modifiers with factors 10/100/1000</source>
        <translation>Stationnement du point final
  - Plage de valeurs 0...longueur de ligne
  - Unité de mesure comme projection de couche
  - ctrl/shift/ctrl+shift clic-➜ facteur 10/100/1000</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="281"/>
        <source>move segment towards reference-line-start-point
   - ctrl/shift/ctrl+shift click-modifiers with factors 10/100/1000</source>
        <translation>Déplacer le segment vers le point de départ de la ligne de référence
    - ctrl/shift/ctrl+shift clic ➜ facteur 10/100/1000</translation>
    </message>
    <message>
        <location filename="../dialogs/LolDialog.py" line="296"/>
        <source>move segment towards reference-line-end-point
   - ctrl/shift/ctrl+shift click-modifiers with factors 10/100/1000</source>
        <translation>Déplacer le segment vers le point final de la ligne de référence
    - ctrl/shift/ctrl+shift clic ➜ facteur 10/100/1000</translation>
    </message>
</context>
<context>
    <name>PolDialog</name>
    <message>
        <location filename="../dialogs/PolDialog.py" line="58"/>
        <source>Linear Referencing: Point-on-Line</source>
        <translation>Linear Referencing: point sur ligne</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="106"/>
        <source>toggle window dockable/undockable</source>
        <translation>Ancrer/détacher la fenêtre</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="116"/>
        <source>Measure:</source>
        <translation>Mesure:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="695"/>
        <source>Reference-Line:</source>
        <translation>Ligne de référence:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="148"/>
        <source>Open Form</source>
        <translation>Formulaire ouvert</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="157"/>
        <source>Zoom to Feature</source>
        <translation>Zoom sur l&apos;ensemble de données</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="187"/>
        <source>Measure (abs/fract):</source>
        <translation>Mesure (abs/fract):</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="195"/>
        <source>Measure as percentage
 - range 0...100</source>
        <translation>Mesure pourcentage
  - Plage de valeurs 0...100</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="265"/>
        <source>Resume measure</source>
        <translation>Mesure sommaire</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="268"/>
        <source>Reset results and start new measure</source>
        <translation>Réinitialiser les résultats, nouvelle mesure</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="274"/>
        <source>Edit:</source>
        <translation>Modifier:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="284"/>
        <source>Edit-PK:</source>
        <translation>Enregistrement sélectionné:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="296"/>
        <source>Update</source>
        <translation>Enregistrer</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="299"/>
        <source>Update selected feature...</source>
        <translation>enregistrer le jeu de données sélectionné...</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="303"/>
        <source>Insert</source>
        <translation>Ajouter</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="306"/>
        <source>Insert feature / duplicate selected feature...</source>
        <translation>Ajouter ou dupliquer enregistrement...</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="311"/>
        <source>Delete</source>
        <translation>Supprimer</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="314"/>
        <source>Delete selected feature...</source>
        <translation>supprimer l&apos;enregistrement de données sélectionné...</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="321"/>
        <source>Feature-Selection:</source>
        <translation>Sélection pour l&apos;édition:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="333"/>
        <source>Select Features</source>
        <translation>Sélectionner des enregistrements</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="337"/>
        <source>Select Features from Show-Layer
    click (point) or drag (rectangle)
    [Shift] â append
    [Ctrl] â remove</source>
        <translation>Sélectionnez afficher les enregistrements de calque
     Point (simple) ou rectangle (sélection multiple)
     [Maj] ➜ Ajouter des enregistrements
     [Ctrl] ➜ Supprimer les enregistrements</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="342"/>
        <source>Insert all Features</source>
        <translation>Ajouter tous les enregistrements de la couche de données</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="345"/>
        <source>Insert all Features from Data-Layer
    [Shift] â append</source>
        <translation>Ajouter tous les enregistrements de la couche de données
     [Maj] ➜ Développer la sélection</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="350"/>
        <source>Insert selected Data-Layer-Features</source>
        <translation>Ajouter sélection de couche de données</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="353"/>
        <source>Insert selected Features from Data-Layer
    [Shift] â append</source>
        <translation>Ajouter les entités sélectionnées de la couche de données
     [Maj] ➜ Développer la sélection</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="358"/>
        <source>Insert selected Show-Layer-Features</source>
        <translation>Ajouter les entités sélectionnées de la couche de préséntation</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="361"/>
        <source>Insert selected Features from Show-Layer
    [Shift] â append</source>
        <translation>Ajouter les entités sélectionnées de la couche de préséntation
     [Maj] ➜ Développer la sélection</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="392"/>
        <source>Zoom to feature-selection</source>
        <translation>Zoom sur la sélection</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="395"/>
        <source>Zoom to selected features</source>
        <translation>Zoom sur la sélection</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="399"/>
        <source>Clear Feature-Selection</source>
        <translation>Réinitialiser la sélection</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="419"/>
        <source>Layers and Fields:</source>
        <translation>Couches et colonnes:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="425"/>
        <source>Reference-Layer...</source>
        <translation>Couche de référence...</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="439"/>
        <source>Linestring-Layer, Geometry-Type linestring/m/z, also Shapfiles with multi-linestring/m/z</source>
        <translation>Couche de référence, renvoie les géométries de lignes, le type de géométrie
    ligne/m/z
    chaîne multiligne/m/z</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="594"/>
        <source>Open Table</source>
        <translation>ouverte table</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="603"/>
        <source>Edit Display-Expression for this Layer</source>
        <translation>Modifier l&apos;expression de préséntation de ce couche</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="520"/>
        <source>      ... ID-Field:</source>
        <translation>      ... Colonne pour ID:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="476"/>
        <source>Field for assignment-key to Data-Layer
type integer or string, typically the PK-Field</source>
        <translation>Colonne de référence à la couche de données
    integer ou string, unique, non nul
    généralement PK-colonne</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="479"/>
        <source>Data-Layer...</source>
        <translation>Couche de données...</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="494"/>
        <source>Geometryless Layer for storing the attributes of point-on-line-features:
	- Reference-Field
	- Measure-Field
Must have a single-column PK</source>
        <translation>Couche d&apos;entités point sur ligne:
    sans géométrie
    modifiable
Colonnes obligatoires :
    ID (PK)
    Référence à la couche de ligne
    mesure</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="607"/>
        <source>...or create</source>
        <translation>...ou créer</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="517"/>
        <source>Create a non-geometry GPKG-Layer for storing measure-data</source>
        <translation>Créer une couche GPKG sans géométrie pour les entités point sur ligne</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="534"/>
        <source>Field with unique key,
type integer or string, typically the PK-Field</source>
        <translation>ID-Colonne
    unique, non nul
    integer ou string
    généralement la colonne PK</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="537"/>
        <source>      ... Reference-Field:</source>
        <translation>      ... Colonne de référence:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="551"/>
        <source>Field for storing the assignment-key to Reference-Layer
type matching to Reference-Layer-ID-Field</source>
        <translation>Colonne de mappage à la couche de référence
    type approprié</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="554"/>
        <source>      ... Measure-Field:</source>
        <translation>      ... Colonne pour mesure:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="568"/>
        <source>Field for storing measure
â distance to the startpoint of the assigned line
numeric data-type</source>
        <translation>Colonne pour mesure
   Distance au point de départ de l&apos;entité linéaire associée
   type numérique</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="571"/>
        <source>Show-Layer...</source>
        <translation>Couche de présentation...</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="585"/>
        <source>Layer to show the point-on-line-Features
Geometry-Type POINT
Source-Type: virtual or ogr (f.e. view in PostGIS or GPKG)</source>
        <translation>Couche représentant les entités point sur ligne:
      couche QGis virtuelle avec requête de couche de référence et de données
      ogr (par exemple vue PostGIS ou GPKG)</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="608"/>
        <source>Create a virtual Layer for showing the results</source>
        <translation>créer une couche virtuelle pour reprentation</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="611"/>
        <source>      ... Back-Reference-Field:</source>
        <translation>      ... colonne de référence arrière:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="625"/>
        <source>Field for Back-Reference to data-layer
Field-Type and contents matching to Data-Layer-ID-Field
typically the PK-Fields in both layers</source>
        <translation>Colonne avec référence arrière à la couche de données
    Type et contenu correspondant au colonne ID de la couche de données
    généralement le PK-colonne dans les deux couches</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="630"/>
        <source>Styles:</source>
        <translation>Modes:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="645"/>
        <source>Symbol</source>
        <translation>Symbole</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="646"/>
        <source>Size</source>
        <translation>Taille</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="647"/>
        <source>Width</source>
        <translation>Large</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="648"/>
        <source>Color</source>
        <translation>Couleur</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="649"/>
        <source>Fill-Color</source>
        <translation>Couleur de remplissage</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="653"/>
        <source>Measure-Point:</source>
        <translation>Point de mesure:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="675"/>
        <source>Edit-Point:</source>
        <translation>Marque d&apos;édition:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="710"/>
        <source>Store/Restore Configurations:</source>
        <translation>Enregistrer/restaurer les configurations:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="717"/>
        <source>Stored Configurations:</source>
        <translation>Configurations enregistrés:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="741"/>
        <source>Measure</source>
        <translation>Mesure</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="742"/>
        <source>Settings</source>
        <translation>Configuration</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="725"/>
        <source>Store current configuration...</source>
        <translation>Enregistrer les paramètres actuels...</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="728"/>
        <source>Restore selected configuration...</source>
        <translation>restaurer la configuration sélectionnée...</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="731"/>
        <source>Delete selected configuration...</source>
        <translation>supprimer la configuration sélectionnée...</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="163"/>
        <source>Cursor-Position x/y:</source>
        <translation>Cursor-Position x/y:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="258"/>
        <source>pan to measure</source>
        <translation>centrer sur le point</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="175"/>
        <source>Snapped-Position x/y:</source>
        <translation>Point de stationnement x/y&#xa0;:</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="190"/>
        <source>Measure in real-world units
 - range 0...length_of_line
 - units accordingly Layer-Projection
 - ctrl/shift/ctrl+shift spinbutton-click-modifiers with factors 10/100/1000</source>
        <translation>Distance au point de départ de la ligne de référence
  - Plage de valeurs 0...longueur de ligne
  - Unité de longueur comme projection de couche
  - ctrl/shift/ctrl+shift clic-➜ facteur 10/100/1000</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="214"/>
        <source>moves segment to reference-line-start-point</source>
        <translation>Déplacer la segment au point de départ de la ligne de référence</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="224"/>
        <source>move segment towards reference-line-start-point
   - ctrl/shift/ctrl+shift click-modifiers with factors 10/100/1000</source>
        <translation></translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="228"/>
        <source>move Point</source>
        <translation>déplacer point</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="232"/>
        <source>move To-Point by mouse-down and drag on selected reference-line</source>
        <translation>Déplacer le point final vers la ligne de référence</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="242"/>
        <source>move segment towards reference-line-end-point
   - ctrl/shift/ctrl+shift click-modifiers with factors 10/100/1000</source>
        <translation>Déplacer le segment dans la direction du point final de la ligne de référence
    - ctrl/shift/ctrl+shift clic-➜ factor10/100/1000</translation>
    </message>
    <message>
        <location filename="../dialogs/PolDialog.py" line="249"/>
        <source>move segment to reference-line-end-point</source>
        <translation>Déplacer la section au point final de la ligne de référence</translation>
    </message>
</context>
<context>
    <name>RuntimeSettings</name>
    <message>
        <location filename="../map_tools/LolEvt.py" line="711"/>
        <source>please select an entry from the list above...</source>
        <translation>Veuillez sélectionner un élément dans la liste ci-dessus...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="684"/>
        <source>Configuration &apos;{setting_label}&apos; restored...</source>
        <translation>Configuration &apos;{setting_label}&apos; restaurée...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="722"/>
        <source>Delete Configuration &apos;{setting_label}&apos;?</source>
        <translation>Supprimer la configuration &apos;{setting_label}&apos;&#xa0;?</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="735"/>
        <source>Configuration &apos;{setting_label}&apos; deleted...</source>
        <translation>Configuration &apos;{setting_label}&apos; supprimée...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3376"/>
        <source>Canceled by user...</source>
        <translation>Annulé par l&apos;utilisateur...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="2996"/>
        <source>LinearReferencing ({gdp()})</source>
        <translation>LinearReferencing ({gdp()})</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="761"/>
        <source>Label for Configuration:</source>
        <translation>Nom pour la configuration:</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="774"/>
        <source>Replace stored Configuration &apos;{new_label}&apos;?</source>
        <translation>Remplacer la configuration stockée &apos;{new_label}&apos;&#xa0;?</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="799"/>
        <source>number of stored settings exceeds maximum ({self._num_storable_settings}), please replace existing one...</source>
        <translation>Le nombre de paramètres enregistrés dépasse le maximum ({self._num_storable_settings}), veuillez en remplacer un existant...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="815"/>
        <source>Current configuration stored under &apos;{new_label}&apos;...</source>
        <translation>Configuration actuelle stockée sous &apos;{new_label}&apos;...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1038"/>
        <source>Null-Values in Offset-Field &apos;{self.ds.dataLyr.name()}.{self.ds.dataLyrOffsetField.name()}&apos;, assumed 0...</source>
        <translation>Valeur nulle dans le colonne de décalage &apos;{self.ds.dataLyr.name()}.{self.ds.dataLyrOffsetField.name()}&apos;, en supposant la valeur 0...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1089"/>
        <source>no reference-feature with ID &apos;{data_feature[self.ds.dataLyrReferenceField.name()]}&apos; in layer {self.ds.refLyr.name()}</source>
        <translation>Aucune référence feature avec FID &apos;{ref_fid}&apos;</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1091"/>
        <source>no data-feature with ID &apos;{edit_pk}&apos; in layer {self.ds.dataLyr.name()}</source>
        <translation>aucun enregistrement avec l&apos;ID &apos;{edit_pk}&apos; dans la couche {self.ds.dataLyr.name()}</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1237"/>
        <source>Missing requirements, reference-, data- and show-layer required...</source>
        <translation>Exigences manquantes, couche de référence, de données et de préséntation nécessaire...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1149"/>
        <source>No selection in data-layer...</source>
        <translation>Aucune sélection dans la couche de données...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1218"/>
        <source>no extent calculable for these features</source>
        <translation>aucune étendue calculable pour ces enregistrements</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1235"/>
        <source>No selection in show-layer...</source>
        <translation>Aucune sélection dans la couche de préséntation...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3298"/>
        <source>Layer &apos;{self.ds.dataLyr.name()}&apos; is editable!

[Yes]        â End edit session with save
[No]         â End edit session without save 
[Cancel]  â Quit...</source>
        <translation>La couche &apos;{self.ds.dataLyr.name()}&apos; est modifiable&#xa0;!

[Oui] ➜ Terminer la session d&apos;édition avec enregistrement
[Non] ➜ Terminer la session d&apos;édition sans enregistrer
[Annuler] ➜ Quitter...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1305"/>
        <source>Feature with ID &apos;{self.rs.edit_pk}&apos; successfully updated in &apos;{self.ds.dataLyr.name()}&apos;...</source>
        <translation>Enregistrement mis à jour avec l&apos;ID &apos;{self.rs.edit_pk}&apos;...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1311"/>
        <source>Update feature failed, measure out of range 0 ... {update_ref_feature.geometry().length()}</source>
        <translation>L&apos;enregistrement de l&apos;ensemble de données a échoué, stationnant en dehors de la plage de valeurs 0 ... {update_ref_feature.geometry().length()}</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1314"/>
        <source>Update feature failed, no reference-feature with PK &apos;{updare_ref_pk}&apos; in layer &apos;{self.ds.refLyr.name()}&apos; ...</source>
        <translation>Échec de la sauvegarde, aucune ligne de référence avec l&apos;ID &apos;{updare_ref_pk}&apos; dans la couche &apos;{self.ds.refLyr.name()}&apos; ...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1323"/>
        <source>Update feature failed, no feature &apos;{self.rs.edit_pk}&apos; in layer &apos;{self.ds.dataLyr.name()}&apos; or reference-feature &apos;{self.rs.snapped_ref_fid}&apos; in layer &apos;{self.ds.refLyr.name()}&apos; ...</source>
        <translation>Échec de la sauvegarde de l&apos;enregistrement, pas d&apos;entité &apos;{self.rs.edit_pk}&apos; dans la couche &apos;{self.ds.dataLyr.name()}&apos; ou d&apos;entité de référence &apos;{self.rs.snapped_ref_fid}&apos; dans la couche &apos;{self.ds .refLyr.nom()}&apos; ...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3262"/>
        <source>Update feature failed, missing privileges in layer &apos;{self.ds.dataLyr.name()}&apos;...</source>
        <translation>Échec de l&apos;enregistrement, manque d&apos;autorisation sur la couche &apos;{self.ds.dataLyr.name()}&apos;...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1360"/>
        <source>No valid reference-feature with fid &apos;{ref_fid}&apos;</source>
        <translation>Aucune référence feature valide avec FID &apos;{ref_fid}&apos;</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1375"/>
        <source>Feature with fid &apos;{ref_fid}&apos; without geometry</source>
        <translation>Jeu de données &apos;{ref_fid}&apos; sans géométrie</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1377"/>
        <source>No Feature with fid &apos;{ref_fid}&apos; in reference-layer</source>
        <translation>Aucun enregistrement avec FID &apos;{ref_fid}&apos; dans la couche de référence</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1410"/>
        <source>Expression &apos;{dlg.expressionText()}&apos; valid and used as DisplayExpression for layer &apos;{self.ds.refLyr.name()}&apos;</source>
        <translation>L&apos;expression &apos;{dlg.expressionText()}&apos; est utilisée comme DisplayExpression pour la couche &apos;{self.ds.refLyr.name()}&apos;</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1412"/>
        <source>Expression &apos;{dlg.expressionText()}&apos; invalid and not used as DisplayExpression for layer &apos;{self.ds.refLyr.name()}&apos;, please check syntax!</source>
        <translation>Expression &apos;{dlg.expressionText()}&apos; incorrecte, veuillez vérifier la syntaxe!</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1415"/>
        <source>No reference-layer defined yet</source>
        <translation>Couche de référence pas encore définie</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1429"/>
        <source>Expression &apos;{dlg.expressionText()}&apos; valid and used as DisplayExpression for layer &apos;{self.ds.dataLyr.name()}&apos;</source>
        <translation>L&apos;expression &apos;{dlg.expressionText()}&apos; est utilisée comme DisplayExpression pour la couche &apos;{self.ds.dataLyr.name()}&apos;</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1431"/>
        <source>Expression &apos;{dlg.expressionText()}&apos; invalid and not used as DisplayExpression for layer &apos;{self.ds.dataLyr.name()}&apos;, please check syntax!</source>
        <translation>Expression &apos;{dlg.expressionText()}&apos; incorrecte, veuillez vérifier la syntaxe!</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1434"/>
        <source>No data-layer defined yet</source>
        <translation>Couche pour data pas encore définie</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1448"/>
        <source>Expression &apos;{dlg.expressionText()}&apos; valid and used as DisplayExpression for layer &apos;{self.ds.showLyr.name()}&apos;</source>
        <translation>L&apos;expression &apos;{dlg.expressionText()}&apos; est utilisée comme DisplayExpression pour la couche &apos;{self.ds.showLyr.name()}&apos;</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1450"/>
        <source>Expression &apos;{dlg.expressionText()}&apos; invalid and not used as DisplayExpression for layer &apos;{self.ds.showLyr.name()}&apos;, please check syntax!</source>
        <translation>Expression &apos;{dlg.expressionText()}&apos; incorrecte, veuillez vérifier la syntaxe!</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1453"/>
        <source>No show-layer defined yet</source>
        <translation>Couche de préséntation pas encore défini</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="1713"/>
        <source>Reference-Feature without Geometry (Reference-Layer &apos;{self.ds.refLyr.name()}&apos;, Field &apos;{self.ds.dataLyrReferenceField.name()}&apos;, Value &apos;{data_feature[self.ds.dataLyrReferenceField.name()]}&apos;)</source>
        <translation>Jeu de données de référence sans géométrie (couche &apos;{self.ds.refLyr.name()}&apos;, colonne &apos;{self.ds.dataLyrReferenceField.name()}&apos;, ID &apos;{data_feature[self.ds.dataLyrReferenceField.name( ) ]}&apos;)</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="2051"/>
        <source>Reference-layer &apos;{reference_layer.name()}&apos; is of type &apos;{wkb_label}&apos;, Line-on-Line-Features on multi-lines are not shown</source>
        <translation>La couche de référence &apos;{reference_layer.name()}&apos; a type &apos;{wkb_label}&apos;, les entités point sur ligne ne peuvent pas être dessinées sur plusieurs lignes</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="2183"/>
        <source>Source-Format of chosen data-layer &apos;{data_layer.name()}&apos; is a file-based office-format (*.xlsx/*.odf), this not recommended...</source>
        <translation>La source de la couche &apos;{data_layer.name()}&apos; est un format bureautique basé sur un fichier (*.xlsx/*.odf), ce n&apos;est pas recommandé...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="2198"/>
        <source>not allowed capabilities: {caps_string}
 â Some editing options will not be available</source>
        <translation>Autorisations manquantes&#xa0;: {caps_string}
  ➜ Options d&apos;édition uniquement disponibles dans une mesure limitée</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="2714"/>
        <source>Missing requirements: No show-layer configured...</source>
        <translation>Conditions préalables manquantes: aucune couche de préséntation définie...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="2860"/>
        <source>LinearReferencing: Select or Create Geo-Package for Line-on-Line-Data</source>
        <translation>LinearReferencing: Select or Create Geo-Package for Line-on-Line-Data</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="2900"/>
        <source>Name for Table in GeoPackage:</source>
        <translation>Nom de la table dans GeoPackage:</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3126"/>
        <source>Canceled by user</source>
        <translation>Annulé par l&apos;utilisateur</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="2905"/>
        <source>Table &apos;{table_name}&apos; already exists in {gpkg_path} !

Replace existing Table?</source>
        <translation>Remplacer la table existante &apos;{table_name}&apos; dans &apos;{gpkg_path}&apos;&#xa0;?</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="2968"/>
        <source>create table &apos;{gpkg_path}&apos;.&apos;{table_name}&apos; successful</source>
        <translation>La table &apos;{gpkg_path}&apos;.&apos;{table_name}&apos; a été créée</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="2971"/>
        <source>Error creating data-layer &apos;{gpkg_path}&apos;.&apos;{table_name}&apos;, created layer not valid</source>
        <translation>Erreur lors de la création de la couche &apos;{gpkg_path}&apos;.&apos;{table_name}&apos;</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="2975"/>
        <source>Error creating data-layer &apos;{gpkg_path}&apos;.&apos;{table_name}&apos;: {writer.errorMessage()}</source>
        <translation>Erreur lors de la création de la couche &apos;{gpkg_path}&apos;.&apos;{table_name}&apos;: {writer.errorMessage()}</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3141"/>
        <source>missing requirements...</source>
        <translation>Conditions préalables manquantes...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="2996"/>
        <source>Name for Virtual Layer:</source>
        <translation>Nom de la couche virtuelle:</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3120"/>
        <source>Virtual layer created and added...</source>
        <translation>Couche virtuelle créée et ajoutée...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3122"/>
        <source>Error creating virtual layer...</source>
        <translation>Erreur lors de la création de la couche virtuelle...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3128"/>
        <source>first create or configure reference- and data-layer</source>
        <translation>Veuillez d&apos;abord créer ou configurer des couches de référence et de données</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3167"/>
        <source>No completed measure yet...</source>
        <translation>Aucune mesure terminée...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3225"/>
        <source>Delete feature with id &apos;{self.rs.edit_pk}&apos; from layer &apos;{self.ds.dataLyr.name()}&apos;?</source>
        <translation>Supprimer l&apos;enregistrement avec l&apos;ID &apos;{self.rs.edit_pk}&apos; dans la couche &apos;{self.ds.dataLyr.name()}&apos;?</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3239"/>
        <source>Feature with ID &apos;{self.rs.edit_pk}&apos; successfully deleted in &apos;{self.ds.dataLyr.name()}&apos;...</source>
        <translation>Enregistrement avec l&apos;ID &apos;{self.rs.edit_pk}&apos; dans la couche &apos;{self.ds.dataLyr.name()}&apos; supprimé...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3259"/>
        <source>Delete feature failed, no feature &apos;{self.rs.edit_pk}&apos; in layer &apos;{self.ds.dataLyr.name()}&apos;...</source>
        <translation>Échec de la suppression de l&apos;enregistrement, aucun enregistrement avec l&apos;ID &apos;{self.rs.edit_pk}&apos; dans la couche &apos;{self.ds.dataLyr.name()}&apos; ou aucun enregistrement référencé &apos;{self.rs.snapped_ref_fid}&apos; dans la couche &apos; {self.ds.refLyr.name()}&apos; ...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3324"/>
        <source>Feature with ID {self.rs.snapped_ref_fid} in Layer &apos;{self.ds.refLyr.name()}&apos; has no value in ID-field {self.ds.refLyrPkField.name()}</source>
        <translation>Enregistrer avec le FID {self.rs.snapped_ref_fid} dans la couche &apos;{self.ds.refLyr.name()}&apos; sans valeur de référence dans le champ {self.ds.refLyrPkField.name()}</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3327"/>
        <source>No reference-feature with ID {self.rs.snapped_ref_fid} in Layer &apos;{self.ds.refLyr.name()}&apos;</source>
        <translation>Aucun enregistrement de référence avec l&apos;ID {self.rs.snapped_ref_fid} dans la couche &apos;{self.ds.refLyr.name()}&apos;</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3370"/>
        <source>New feature with ID &apos;{used_pk}&apos; successfully added to &apos;{self.ds.dataLyr.name()}&apos;...</source>
        <translation>Ensemble de données ajouté avec l&apos;ID &apos;{used_pk}&apos; dans la couche &apos;{self.ds.dataLyr.name()}&apos;...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3384"/>
        <source>Add feature failed, missing privileges in layer &apos;{self.ds.dataLyr.name()}&apos;...</source>
        <translation>L&apos;ensemble de données dans la couche &apos;{self.ds.dataLyr.name()}&apos; n&apos;a pas pu être créé, privilèges manquants...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="3511"/>
        <source>tool_mode &apos;{tool_mode}&apos; not implemented...</source>
        <translation>tool_mode &apos;{tool_mode}&apos; non implémenté...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="4394"/>
        <source>Remove Feature from Selection</source>
        <translation>Supprimer l&apos;enregistrement de la sélection</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="4403"/>
        <source>Highlight Feature and Select for Edit</source>
        <translation>Mettez en surbrillance l&apos;enregistrement et sélectionnez-le pour le modifier</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="4412"/>
        <source>Pan to Feature and Select for Edit</source>
        <translation>Zoomer sur le jeu de données et sélectionner pour l&apos;édition</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="4421"/>
        <source>Show Feature-Form</source>
        <translation>Ouvrir le formulaire d&apos;enregistrement</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="4450"/>
        <source>Highlight Reference-Feature</source>
        <translation>Mettre en surbrillance la forme de la ligne</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="4459"/>
        <source>Zoom to Reference-Feature</source>
        <translation>Zoom sur la forme de la ligne</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="4468"/>
        <source>Show Reference-Feature-Form</source>
        <translation>Ouvrir le formulaire d&apos;enregistrement de référence</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="4502"/>
        <source>Show Show-Feature-Form</source>
        <translation>Ouvrir le formulaire d&apos;enregistrement des données de représentation</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="4564"/>
        <source>no feature with ID &apos;{edit_pk}&apos; in data-layer {self.ds.dataLyr.name()}</source>
        <translation>Aucun enregistrement avec l&apos;ID &apos;{edit_pk}&apos; dans la couche {self.ds.dataLyr.name()}</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="4601"/>
        <source>no feature with value &apos;{edit_pk}&apos; in back-reference-field &apos;{self.ds.showLyrBackReferenceField.name()}&apos; of show-layer &apos;{self.ds.showLyr.name()}&apos;</source>
        <translation>Aucun enregistrement avec la valeur &apos;{edit_pk}&apos; dans le champ de référence arrière &apos;{self.ds.showLyrBackReferenceField.name()}&apos; de la couche &apos;{self.ds.showLyr.name()}&apos;</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="4652"/>
        <source>no feature with value &apos;{data_feature[self.ds.dataLyrReferenceField.name()]}&apos; in field &apos;{self.ds.dataLyrReferenceField.name()}&apos; of layer &apos;{self.ds.refLyr.name()}&apos;</source>
        <translation>Aucun enregistrement avec la valeur &apos;{data_feature[self.ds.dataLyrReferenceField.name()]}&apos; dans le champ &apos;{self.ds.dataLyrReferenceField.name()}&apos; de la couche &apos;{self.ds.refLyr.name()}&apos;</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="4627"/>
        <source>Reference-feature without geometry (Reference-Layer &apos;{self.ds.refLyr.name()}&apos;, field &apos;{self.ds.dataLyrReferenceField.name()}&apos;, value &apos;{data_feature[self.ds.dataLyrReferenceField.name()]}&apos;)</source>
        <translation>Jeu de données de référence sans géométrie (couche &apos;{self.ds.refLyr.name()}&apos;, champ &apos;{self.ds.dataLyrReferenceField.name()}&apos;, valeur &apos;{data_feature[self.ds.dataLyrReferenceField.name() ] ]}&apos;)</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="4650"/>
        <source>Reference-feature without geometry (layer &apos;{self.ds.refLyr.name()}&apos;, field &apos;{self.ds.dataLyrReferenceField.name()}&apos;, value &apos;{data_feature[self.ds.dataLyrReferenceField.name()]}&apos;)</source>
        <translation>Jeu de données de référence sans géométrie (couche &apos;{self.ds.refLyr.name()}&apos;, champ &apos;{self.ds.dataLyrReferenceField.name()}&apos;, valeur &apos;{data_feature[self.ds.dataLyrReferenceField.name()]]}&apos;)</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="460"/>
        <source>Initializing, please wait...</source>
        <translation>Initialisation, veuillez patienter...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="462"/>
        <source>hover + left-mouse-down on map to snap reference-line and measure the from-point...</source>
        <translation></translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="463"/>
        <source>hold left mouse-button, drag to desired to-point, release mouse-button to measure the to-point...</source>
        <translation>Déplacez le point avec le bouton de la souris enfoncé et relâchez-le...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="464"/>
        <source>measure ended, see results in dialog, edit segment, add feature to data-layer or resume for next measure...</source>
        <translation>Mesure terminée, modifiez et/ou enregistrez les résultats dans la boîte de dialogue, cliquez sur la carte pour une nouvelle mesure...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="466"/>
        <source>mouse-down on canvas and move from-point to the desired location on reference-line...</source>
        <translation>Déplacer le point de départ vers la ligne de référence...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="467"/>
        <source>mouse-release to position from-point on snapped reference-line...</source>
        <translation>Relâchez le bouton de la souris à la position cible de la ligne de référence...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="469"/>
        <source>mouse-down on canvas and move to-point to the desired location on reference-line......</source>
        <translation>Déplacer le point final vers la ligne de référence...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="470"/>
        <source>mouse-release to position to-point on snapped reference-line...</source>
        <translation>Relâchez le bouton de la souris à la position cible de la ligne de référence...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="472"/>
        <source>click the segment and start dragging, supports [ctrl] or [shift] modifiers...</source>
        <translation>Cliquez et déplacez le segment sur la carte, variantes [ctrl] ou [shift]...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="473"/>
        <source>drag and release the selected segment, supports [ctrl] or [shift] modifiers...</source>
        <translation>Déplacer le segment sur la carte, relâcher le bouton de la souris, variantes [ctrl] ou [Maj]...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="475"/>
        <source>no reference-layer (linestring) found or configured, check settings...</source>
        <translation>Aucune couche de référence configurée...</translation>
    </message>
    <message>
        <location filename="../map_tools/LolEvt.py" line="477"/>
        <source>click or draw rect to select features for edit</source>
        <translation>Cliquez sur les éléments souhaités ou sélectionnez avec un rectangle</translation>
    </message>
</context>
<context>
    <name>mt</name>
    <message>
        <location filename="../map_tools/FeatureActions.py" line="155"/>
        <source>no valid feature for FID {fid} in Layer &apos;{layer_id}&apos;...</source>
        <translation>aucun enregistrement valide avec le FID {fid} dans la couche &apos;{layer_id}&apos;...</translation>
    </message>
    <message>
        <location filename="../map_tools/FeatureActions.py" line="157"/>
        <source>Missing configuration Show-layer-&gt;Back-Reference-Field...</source>
        <translation>Configuration manquante : Couche de préséntation➜Colonne de référence arrière...</translation>
    </message>
    <message>
        <location filename="../map_tools/FeatureActions.py" line="161"/>
        <source>layer &apos;{data_or_show_lyr}&apos; not registered as data-layer or show-layer, please redefine layers in plugin-dialogue!</source>
        <translation>La couche &apos;{data_or_show_lyr}&apos; n&apos;est pas configurée en tant que couche de données ou préséntation!</translation>
    </message>
</context>
</TS>
