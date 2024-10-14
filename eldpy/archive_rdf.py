def write_metadata_rdf(self):
        archive = self.name
        eaf_template = "%s-%s"
        g = lod.create_graph()
        g.add((lod.QUESTRESOLVER[archive], RDF.type, lod.QUEST.Archive))
        for collection in self.collections:
            g.add((lod.QUESTRESOLVER[collection], RDF.type, lod.QUEST.Collection))
            g.add(
                (
                    lod.QUESTRESOLVER[collection],
                    lod.DBPEDIA.isPartOf,
                    lod.QUESTRESOLVER[archive],
                )
            )
            # print(collection, len(self.collections[collection].elanfiles))
            for eafname in self.collections[collection].elanfiles:
                hashed_eaf = self.get_eaf_hash(eafname.url)
                eaf_id = eaf_template % (collection, hashed_eaf)
                g.add(
                    (
                        lod.QUESTRESOLVER[
                            eaf_id
                        ],  # TODO better use archive specific resolvers
                        RDF.type,
                        # lod.QUEST.Elan_file
                        lod.LIGT.InterlinearText,
                    )
                )
                g.add((lod.QUESTRESOLVER[eaf_id], RDFS.label, Literal(eafname)))
                g.add(
                    (
                        lod.QUESTRESOLVER[eaf_id],
                        lod.DBPEDIA.isPartOf,
                        lod.QUESTRESOLVER[collection],
                    )
                )
        print(len(g), "metadata triples")
        lod.write_graph(g, "rdf/%s-metadata.n3" % self.name)

    def get_eaf_hash(self, eafname):
        eafbasename = eafname.split("/")[-1]
        hashed_eaf = str(hash(eafbasename))[-7:]

        return hashed_eaf

    def write_transcriptions_rdf(self):
        ID_template = "%s-%s-transcription-%s-%s"
        # FIXME transcriptions and translations should probably point to the same tier
        # but we must make sure that he offsets match. Better use the annotation_ID of the time-aligned ancestor, which should be shared
        eaf_template = "%s-%s"
        g = lod.create_graph()
        for collection in self.collections:
            collection_id = self.collections[collection].ID
            for eafname in self.collections[collection].transcriptions:
                hashed_eaf = self.get_eaf_hash(eafname)
                eaf_id = eaf_template % (collection_id, hashed_eaf)
                for i, tier in enumerate(
                    self.collections[collection].transcriptions[eafname]
                ):
                    for j, annotation in enumerate(tier):
                        tier_id = ID_template % (collection_id, hashed_eaf, i, j)
                        g.add(
                            (
                                lod.QUESTRESOLVER[
                                    tier_id
                                ],  # TODO better use archive specific resolvers
                                RDF.type,
                                # lod.QUEST.Transcripton_tier
                                lod.LIGT.Utterance,
                            )
                        )
                        g.add(
                            (
                                lod.QUESTRESOLVER[tier_id],
                                RDFS.label,
                                Literal(
                                    "%s" % annotation.strip(), lang="und"
                                ),  # we use und_efined until we can retrieve metatdata
                            )
                        )
                        g.add(
                            (
                                lod.ARCHIVE_NAMESPACES[self.name.lower()][eaf_id],
                                lod.LIGT.hasTier,  # check for tier-file, file-collection and tier-collection meronymic relations
                                lod.QUESTRESOLVER[tier_id],
                            )
                        )
        print(len(g), "transcription triples")
        lod.write_graph(g, "rdf/%s-transcriptions.n3" % self.name)

    def write_translations_rdf(self):
        ID_template = "%s-%s-translation-%s-%s"
        eaf_template = "%s-%s"
        # FIXME transcriptions and translations should probably point to the same tier
        # but we must make sure that he offsets match. Better use the annotation_ID of the time-aligned ancestor, which should be shared
        g = lod.create_graph()
        for collection in self.collections:
            for eafname in self.collections[collection].translations:
                hashed_eaf = self.get_eaf_hash(eafname)
                eaf_id = eaf_template % (collection, hashed_eaf)
                for i, tier in enumerate(
                    self.collections[collection].translations[eafname]
                ):
                    for j, annotation in enumerate(tier):
                        tier_id = ID_template % (collection, hashed_eaf, i, j)
                        g.add(
                            (
                                lod.QUESTRESOLVER[
                                    tier_id
                                ],  # TODO better use archive specific resolvers
                                RDF.type,
                                # lod.QUEST.Translation_tier
                                lod.LIGT.Utterance,
                            )
                        )
                        g.add(
                            (
                                lod.QUESTRESOLVER[tier_id],
                                RDFS.label,
                                Literal("%s" % annotation.strip(), lang="eng"),
                            )
                        )
                        g.add(
                            (
                                lod.QUESTRESOLVER[tier_id],
                                lod.LIGT.subSegment,  # check for tier-file, file-collection and tier-collection meronymic relations
                                lod.ARCHIVE_NAMESPACES[self.name.lower()][eaf_id],
                            )
                        )
        print(len(g), "translation triples")
        lod.write_graph(g, "rdf/%s-translations.n3" % self.name)

    def write_glosses_rdf(self):
        # https://github.com/acoli-repo/ligt/blob/master/samples/nordhoff-1.ttl
        example_ID_template = "%s-%s-%s_u"
        word_tier_ID_template = "%s-%s-%s_wt"
        morph_tier_ID_template = "%s-%s-%s_mt"
        word_template = "%s-%s-%s-%s_w"
        morph_ID_template = "%s-%s-%s-%s_m"
        gloss_template = "%s-%s-%s-%s_g"
        eaf_template = "%s-%s"
        g = lod.create_graph()
        g.add(
            (
                lod.QUEST.morph2,  # TODO needs better label
                lod.RDFS.subPropertyOf,
                lod.LIGT.annotation,
            )
        )
        g.add(
            (
                lod.QUEST.gloss2,  # TODO needs better label
                lod.RDFS.subPropertyOf,
                lod.LIGT.annotation,
            )
        )
        for collection in self.collections:
            for eafname in self.collections[collection].glosses:
                hashed_eaf = self.get_eaf_hash(eafname)
                eaf_id = eaf_template % (collection, hashed_eaf)
                for tiertype in self.collections[collection].glosses[eafname]:
                    for tierID in self.collections[collection].glosses[eafname][
                        tiertype
                    ]:
                        for dictionary in self.collections[collection].glosses[eafname][
                            tiertype
                        ][tierID]:
                            for sentenceID in dictionary:
                                example_block_ID = example_ID_template % (
                                    collection,
                                    hashed_eaf,
                                    sentenceID,
                                )
                                sentence_word_tier_lod_ID = word_tier_ID_template % (
                                    collection,
                                    hashed_eaf,
                                    sentenceID,
                                )
                                sentence_morph_tier_lod_ID = word_tier_ID_template % (
                                    collection,
                                    hashed_eaf,
                                    sentenceID,
                                )
                                wordstring = " ".join(
                                    [
                                        "" if t[0] is None else t[0]
                                        for t in dictionary[sentenceID]
                                    ]
                                )
                                glossstring = " ".join(
                                    [
                                        "" if t[1] is None else t[1]
                                        for t in dictionary[sentenceID]
                                    ]
                                )
                                example_block_nif_label = wordstring
                                words_nif_label = wordstring
                                vernacular_language_id = "und"
                                gloss_language_id = "en-x-lgr"
                                g.add(
                                    (
                                        lod.ARCHIVE_NAMESPACES[self.name.lower()][
                                            eaf_id
                                        ],
                                        lod.LIGT.hasTier,
                                        lod.QUESTRESOLVER[example_block_ID],
                                    )
                                )
                                # example block (=utterance in LIGT lingo)
                                g.add(
                                    (
                                        lod.QUESTRESOLVER[example_block_ID],
                                        # TODO better use archive specific resolvers
                                        RDF.type,
                                        lod.LIGT.InterlinearText,
                                    )
                                )
                                g.add(
                                    (
                                        lod.QUESTRESOLVER[example_block_ID],
                                        RDF.type,
                                        lod.LIGT.Utterance,
                                    )
                                )
                                g.add(
                                    (
                                        lod.QUESTRESOLVER[example_block_ID],
                                        lod.NIF.anchorOf,
                                        Literal(
                                            example_block_nif_label,
                                            lang=vernacular_language_id,
                                        ),
                                    )
                                )
                                g.add(
                                    (
                                        lod.QUESTRESOLVER[example_block_ID],
                                        lod.LIGT.hasTier,
                                        lod.QUESTRESOLVER[sentence_word_tier_lod_ID],
                                    )
                                )
                                g.add(
                                    (
                                        lod.QUESTRESOLVER[example_block_ID],
                                        lod.LIGT.hasTier,
                                        lod.QUESTRESOLVER[sentence_morph_tier_lod_ID],
                                    )
                                )
                                # words
                                g.add(
                                    (
                                        lod.QUESTRESOLVER[sentence_word_tier_lod_ID],
                                        RDF.type,
                                        lod.LIGT.WordTier,
                                    )
                                )
                                g.add(
                                    (
                                        lod.QUESTRESOLVER[sentence_word_tier_lod_ID],
                                        lod.NIF.anchorOf,
                                        Literal(
                                            example_block_ID,
                                            lang=vernacular_language_id,
                                        ),
                                    )
                                )
                                # morphs
                                g.add(
                                    (
                                        lod.QUESTRESOLVER[sentence_morph_tier_lod_ID],
                                        RDF.type,
                                        lod.LIGT.MorphTier,
                                    )
                                )
                                g.add(
                                    (
                                        lod.QUESTRESOLVER[sentence_morph_tier_lod_ID],
                                        lod.NIF.anchorOf,
                                        Literal(
                                            example_block_ID,
                                            lang=vernacular_language_id,
                                        ),
                                    )
                                )
                                # subelements of word, morph and gloss tier
                                # TODO unclear whether we need word tier
                                morphs = [
                                    t[0] if t[0] else "" for t in dictionary[sentenceID]
                                ]
                                glosses = [
                                    t[1] if t[1] else "" for t in dictionary[sentenceID]
                                ]
                                for i in range(len(morphs)):
                                    morph = morphs[i]
                                    morph_id = morph_ID_template % (
                                        collection,
                                        hashed_eaf,
                                        sentenceID,
                                        i,
                                    )
                                    gloss = glosses[i]
                                    try:
                                        gloss = gloss.strip()
                                    except TypeError:
                                        gloss = ""
                                    # add items to tier
                                    g.add(
                                        (
                                            lod.QUESTRESOLVER[
                                                sentence_morph_tier_lod_ID
                                            ],
                                            lod.LIGT.item,
                                            lod.QUESTRESOLVER[morph_id],
                                        )
                                    )
                                    # anchor in superstring about items
                                    g.add(
                                        (
                                            lod.QUESTRESOLVER[morph_id],
                                            lod.NIF.anchorOf,
                                            lod.QUESTRESOLVER[
                                                sentence_word_tier_lod_ID
                                            ],  # TODO this should probably sentence_word_id, but we have no notion of "word" right now, hence resorting to a larger substring
                                        )
                                    )
                                    # forward link to create linked list
                                    try:
                                        nextmorph = morphs[i + 1]
                                        nextmorph_id = urllib.parse.quote(
                                            morph_ID_template
                                            % (
                                                collection,
                                                hashed_eaf,
                                                sentenceID,
                                                i + 1,
                                            )
                                        )
                                        g.add(
                                            (
                                                lod.QUESTRESOLVER[morph_id],
                                                lod.LIGT.nextWord,
                                                lod.QUESTRESOLVER[nextmorph_id],
                                            )
                                        )
                                    except (
                                        IndexError
                                    ):  # we have reached the end of the list
                                        g.add(
                                            (
                                                lod.QUESTRESOLVER[morph_id],
                                                lod.LIGT.nextWord,
                                                lod.RDF.nil,
                                            )
                                        )
                                    # give labels for morphs
                                    g.add(
                                        (
                                            lod.QUESTRESOLVER[morph_id],
                                            lod.QUEST.morph2,  # TODO probably use not   "morph2" here
                                            Literal(morph, lang=vernacular_language_id),
                                        )
                                    )
                                    g.add(
                                        (
                                            lod.QUESTRESOLVER[morph_id],
                                            lod.QUEST.gloss2,  # TODO probably use not   "gloss2" here
                                            Literal(gloss, lang=gloss_language_id),
                                        )
                                    )
                                    for subgloss in re.split("[-=.:]", gloss):
                                        subgloss = (
                                            subgloss.replace("1", "")
                                            .replace("2", "")
                                            .replace("3", "")
                                        )
                                        if subgloss in lod.LGRLIST:
                                            g.add(
                                                (
                                                    lod.QUESTRESOLVER[morph_id],
                                                    lod.QUEST.has_lgr_value,
                                                    lod.LGR[subgloss],
                                                )
                                            )

                                # TODO not sure in how far the specific ligt modeling from 2019 is needed anymore
                                # for i, gloss in enumerate(glosses):
                                # vernacular = vernaculars[i]
                                # try:
                                # gloss = gloss.strip()
                                # except TypeError:
                                # gloss = ""
                                # gloss_id = urllib.parse.quote(
                                # gloss_template % (collection, hashed_eaf, sentenceID, i)
                                # )
                                # g.add((lod.QUESTRESOLVER[gloss_id],
                                # RDF.type,
                                ## lod.QUEST.gloss
                                # lod.LIGT.Word,
                                # ))
                                # g.add((lod.QUESTRESOLVER[gloss_id],
                                # lod.FLEX.gls,
                                # Literal(gloss, lang="eng"),
                                ## we use qqq since glossed text is not natural language
                                # ))
                                # g.add((lod.QUESTRESOLVER[gloss_id],
                                # lod.FLEX.txt,
                                # Literal(vernacular, lang="und"),
                                ## we use "und" until we can retrieve the proper metadata
                                # ))
                                # g.add((lod.QUESTRESOLVER[sentence_lod_ID],
                                # lod.LIGT.hasWord,
                                # lod.QUESTRESOLVER[gloss_id],
                                # ))
        print(len(g), "gloss triples")
        lod.write_graph(g, "rdf/%s-glosses.n3" % self.name)

    def write_entities_rdf(self):
        ID_template = "%s-%s-%s"
        eaf_template = "%s-%s"
        g = lod.create_graph()
        for collection in self.collections:
            for eafname in self.collections[collection].entities:
                hashed_eaf = self.get_eaf_hash(eafname)
                eaf_id = eaf_template % (collection, hashed_eaf)
                for i, tier in enumerate(
                    self.collections[collection].entities[eafname]
                ):
                    tier_id = ID_template % (collection, hashed_eaf, i)
                    g.add(
                        (
                            lod.QUESTRESOLVER[tier_id],
                            lod.LIGT.subSegment,
                            lod.QUESTRESOLVER[eaf_id],
                        )
                    )
                    for q_value in tier:
                        g.add(
                            (
                                lod.QUESTRESOLVER[
                                    tier_id
                                ],  # TODO better use archive specific resolvers
                                lod.DC.subject,
                                lod.WIKIDATA[q_value],
                            )
                        )
        print(len(g), "entity triples")
        lod.write_graph(g, "rdf/%s-entities.n3" % self.name)

    def write_rdf(self):
        print("writing rdf for", self.name)
        print("  meta")
        self.write_metadata_rdf()
        print("  transcriptions")
        self.write_transcriptions_rdf()
        print("  glosses")
        self.write_glosses_rdf()
        print("  translations")
        self.write_translations_rdf()
        print("  entities")
        self.write_entities_rdf()
        print("  done")
