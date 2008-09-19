--
-- PostgreSQL database dump
--

SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

SET search_path = public, pg_catalog;

--
-- Name: cals_category_id_seq; Type: SEQUENCE SET; Schema: public; Owner: cals
--

SELECT pg_catalog.setval('"cals_category_id_seq"', 11, true);


--
-- Name: cals_feature_id_seq; Type: SEQUENCE SET; Schema: public; Owner: cals
--

SELECT pg_catalog.setval('"cals_feature_id_seq"', 142, true);


--
-- Name: cals_featurevalue_id_seq; Type: SEQUENCE SET; Schema: public; Owner: cals
--

SELECT pg_catalog.setval('"cals_featurevalue_id_seq"', 143, true);


--
-- Name: cals_language_features_id_seq; Type: SEQUENCE SET; Schema: public; Owner: cals
--

SELECT pg_catalog.setval('"cals_language_features_id_seq"', 5, true);


--
-- Name: cals_language_id_seq; Type: SEQUENCE SET; Schema: public; Owner: cals
--

SELECT pg_catalog.setval('"cals_language_id_seq"', 1, true);


--
-- Name: auth_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: cals
--

SELECT pg_catalog.setval('auth_group_id_seq', 1, false);


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: cals
--

SELECT pg_catalog.setval('auth_group_permissions_id_seq', 1, false);


--
-- Name: auth_message_id_seq; Type: SEQUENCE SET; Schema: public; Owner: cals
--

SELECT pg_catalog.setval('auth_message_id_seq', 1, false);


--
-- Name: auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: cals
--

SELECT pg_catalog.setval('auth_permission_id_seq', 36, true);


--
-- Name: auth_user_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: cals
--

SELECT pg_catalog.setval('auth_user_groups_id_seq', 1, false);


--
-- Name: auth_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: cals
--

SELECT pg_catalog.setval('auth_user_id_seq', 1, true);


--
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: cals
--

SELECT pg_catalog.setval('auth_user_user_permissions_id_seq', 1, false);


--
-- Name: django_admin_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: cals
--

SELECT pg_catalog.setval('django_admin_log_id_seq', 1, false);


--
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: cals
--

SELECT pg_catalog.setval('django_content_type_id_seq', 12, true);


--
-- Name: django_site_id_seq; Type: SEQUENCE SET; Schema: public; Owner: cals
--

SELECT pg_catalog.setval('django_site_id_seq', 1, true);


--
-- Data for Name: cals_category; Type: TABLE DATA; Schema: public; Owner: cals
--

COPY "cals_category" (id, name) FROM stdin;
1	Phonology
2	Morphology
3	Nominal Categories
4	Nominal Syntax
5	Verbal Categories
6	Word Order
7	Simple Clauses
8	Complex Sentences
9	Lexicon
10	Sign Languages
11	Other
\.


--
-- Data for Name: cals_feature; Type: TABLE DATA; Schema: public; Owner: cals
--

COPY "cals_feature" (id, name, category_id) FROM stdin;
1	Consonant Inventories	1
2	Vowel Quality Inventories	1
3	Consonant-Vowel Ratio	1
4	Voicing in Plosives and Fricatives	1
5	Voicing and Gaps in Plosive Systems	1
6	Uvular Consonants	1
7	Glottalized Consonants	1
8	Lateral Consonants	1
9	The Velar Nasal	1
10	Vowel Nasalization	1
11	Front Rounded Vowels	1
12	Syllable Structure	1
13	Tone	1
14	Fixed Stress Locations	1
15	Weight-Sensitive Stress	1
16	Weight Factors in Weight-Sensitive Stress Systems	1
17	Rhythm Types	1
18	Absence of Common Consonants	1
19	Presence of Uncommon Consonants	1
20	Fusion of Selected Inflectional Formatives	2
21	Exponence of Selected Inflectional Formatives	2
22	Inflectional Synthesis of the Verb	2
23	Locus of Marking in the Clause	2
24	Locus of Marking in Possessive Noun Phrases	2
25	Locus of Marking: Whole-language Typology	2
26	Prefixing vs. Suffixing in Inflectional Morphology	2
27	Reduplication	2
28	Case Syncretism	2
29	Syncretism in Verbal Person/Number Marking	2
30	Number of Genders	3
31	Sex-based and Non-sex-based Gender Systems	3
32	Systems of Gender Assignment	3
33	Coding of Nominal Plurality	3
34	Occurrence of Nominal Plurality	3
35	Plurality in Independent Personal Pronouns	3
36	The Associative Plural	3
37	Definite Articles	3
38	Indefinite Articles	3
39	Inclusive/Exclusive Distinction in Independent Pronouns	3
40	Inclusive/Exclusive Distinction in Verbal Inflection	3
41	Distance Contrasts in Demonstratives	3
42	Pronominal and Adnominal Demonstratives	3
43	Third Person Pronouns and Demonstratives	3
44	Gender Distinctions in Independent Personal Pronouns	3
45	Politeness Distinctions in Pronouns	3
46	Indefinite Pronouns	3
47	Intensifiers and Reflexive Pronouns	3
48	Person Marking on Adpositions	3
49	Number of Cases	3
50	Asymmetrical Case-Marking	3
51	Position of Case Affixes	3
52	Comitatives and Instrumentals	3
53	Ordinal Numerals	3
54	Distributive Numerals	3
55	Numeral Classifiers	3
56	Conjunctions and Universal Quantifiers	3
57	Position of Pronominal Possessive Affixes	3
58	Obligatory Possessive Inflection	4
59	Possessive Classification	4
60	Genitives, Adjectives and Relative Clauses	4
61	Adjectives without Nouns	4
62	Action Nominal Constructions	4
63	Noun Phrase Conjunction	4
64	Nominal and Verbal Conjunction	4
65	Perfective/Imperfective Aspect	5
66	The Past Tense	5
67	The Future Tense	5
68	The Perfect	5
69	Position of Tense-Aspect Affixes	5
70	The Morphological Imperative	5
71	The Prohibitive	5
72	Imperative-Hortative Systems	5
73	The Optative	5
74	Situational Possibility	5
75	Epistemic Possibility	5
76	Overlap between Situational and Epistemic Modal Marking	5
77	Semantic Distinctions of Evidentiality	5
78	Coding of Evidentiality	5
79	Suppletion According to Tense and Aspect	5
80	Verbal Number and Suppletion	5
81	Order of Subject, Object and Verb	6
82	Order of Subject and Verb	6
83	Order of Object and Verb	6
84	Order of Object, Oblique, and Verb	6
85	Order of Adposition and Noun Phrase	6
86	Order of Genitive and Noun	6
87	Order of Adjective and Noun	6
88	Order of Demonstrative and Noun	6
89	Order of Numeral and Noun	6
90	Order of Relative Clause and Noun	6
91	Order of Degree Word and Adjective	6
92	Position of Polar Question Particles	6
93	Position of Interrogative Phrases in Content Questions	6
94	Order of Adverbial Subordinator and Clause	6
95	Relationship between the Order of Object and Verb and the Order of Adposition and Noun Phrase	6
96	Relationship between the Order of Object and Verb and the Order of Relative Clause and Noun	6
97	Relationship between the Order of Object and Verb and the Order of Adjective and Noun	6
98	Alignment of Case Marking of Full Noun Phrases	7
99	Alignment of Case Marking of Pronouns	7
100	Alignment of Verbal Person Marking	7
101	Expression of Pronominal Subjects	7
102	Verbal Person Marking	7
103	Third Person Zero of Verbal Person Marking	7
104	Order of Person Markers on the Verb	7
105	Ditransitive Constructions: The Verb 'Give'	7
106	Reciprocal Constructions	7
107	Passive Constructions	7
108	Antipassive Constructions	7
109	Applicative Constructions	7
110	Periphrastic Causative Constructions	7
111	Nonperiphrastic Causative Constructions	7
112	Negative Morphemes	7
113	Symmetric and Asymmetric Standard Negation	7
114	Subtypes of Asymmetric Standard Negation	7
115	Negative Indefinite Pronouns and Predicate Negation	7
116	Polar Questions	7
117	Predicative Possession	7
118	Predicative Adjectives	7
119	Nominal and Locational Predication	7
120	Zero Copula for Predicate Nominals	7
121	Comparative Constructions	7
122	Relativization on Subjects	8
123	Relativization on Obliques	8
124	'Want' Complement Subjects	8
125	Purpose Clauses	8
126	'When' Clauses	8
127	Reason Clauses	8
128	Utterance Complement Clauses	8
129	Hand and Arm	9
130	Finger and Hand	9
131	Numeral Bases	9
132	Number of Non-Derived Basic Colour Categories	9
133	Number of Basic Colour Categories	9
134	Green and Blue	9
135	Red and Yellow	9
136	M-T Pronouns	9
137	N-M Pronouns	9
138	Tea	9
139	Irregular Negatives in Sign Languages	10
140	Question Particles in Sign Languages	10
141	Writing Systems	11
142	Para-Linguistic Usages of Clicks	11
\.


--
-- Data for Name: cals_featurevalue; Type: TABLE DATA; Schema: public; Owner: cals
--

COPY "cals_featurevalue" (id, feature_id, name) FROM stdin;
1	1	Small
2	1	Moderately small
3	1	Average
4	1	Moderately large
5	1	Large
6	2	Small (2-4)
7	2	Average (5-6)
8	2	Large (7-14)
9	3	Low
10	3	Moderately low
11	3	Average
12	3	Moderately high
13	3	High
14	4	No voicing constrast
15	4	In plosives alone
16	4	In fricatives alone
17	4	 In both plosives and fricatives
18	5	Other
19	5	None missing in /p t k b d g/
20	5	Missing /p/
21	5	Missing /g/
22	5	Both missing
23	6	Uvular stops only
24	6	Uvular continuants only
25	6	Uvular stops and continuants
26	7	No glottalized consonants
27	7	Ejectives only
28	7	Implosives only
29	7	Glottalized resonants only
30	7	Ejectives and implosives
31	7	Ejectives and glottalized resonants
32	7	Implosives and glottalized resonants
33	7	Ejectives, implosives, and glottalized resonants
34	8	No laterals
35	8	/l/, no obstruent laterals
36	8	Laterals, but no /l/, no obstruent laterals
37	8	/l/ and lateral obstruent
38	8	No /l/, but lateral obstruents
39	9	Initial velar nasal
40	9	No initial velar nasal
41	9	No velar nasal
42	10	Contrast present
43	10	Contrast absent
44	11	None
45	11	High and mid
46	11	High only
47	11	Mid only
48	12	Simple
49	12	Moderately complex
50	12	Complex
51	13	No tones
52	13	Simple tone system
53	13	Complex tone system     
54	14	No fixed stress
55	14	Initial
56	14	Second
57	14	Third
58	14	Antepenultimate
59	14	Penultimate
60	14	Ultimate
61	15	Left-edge: First or second
62	15	Left-oriented: One of the first three
63	15	Right-edge: Ultimate or penultimate
64	15	Right-oriented: One of the last three
65	15	Unbounded: Stress can be anywhere
66	15	Combined: Right-edge and unbounded
67	15	Not predictable
68	15	Fixed stress
69	16	No weight
70	16	Long vowel
71	16	Coda consonant
72	16	Long vowel or coda consonant
73	16	Prominence
74	16	Lexical stress
75	16	Combined
76	17	Trochaic
77	17	Iambic
78	17	Dual: both trochaic and iambic
79	17	Undetermined
80	17	No rhythmic stress
81	18	All present
82	18	No bilabials
83	18	No fricatives
84	18	No nasals
85	18	No bilabials or nasals
86	18	No fricatives or nasals
87	19	None
88	19	Clicks
89	19	Labial-velars
90	19	Pharyngeals
91	19	'Th' sounds
92	19	Clicks, pharyngeals, and 'th'
93	19	Pharyngeals and 'th'
94	20	Exclusively concatenative
95	20	Exclusively isolating
96	20	Exclusively tonal
97	20	Tonal/isolating
98	20	Tonal/concatenative
99	20	Ablaut/concatenative
100	20	Isolating/concatenative
101	21	Monoexponential case
102	21	Case + number
103	21	Case + referentiality
104	21	Case + TAM
105	21	No case
106	22	0-1 category per word
107	22	2-3 categories per word
108	22	4-5 categories per word
109	22	6-7 categories per word
110	22	8-9 categories per word
111	22	10-11 categories per word
112	22	12-13 categories per word
113	23	Head marking
114	23	Dependent marking
115	23	Double marking
116	23	No marking
117	23	Other
118	24	Head marking
119	24	Dependent marking
120	24	Double marking
121	24	No marking
122	24	Other
123	25	Head-marking
124	25	Dependent-marking
125	25	Double-marking
126	25	Zero-marking
127	25	Inconsistent or other
128	26	Little affixation
129	26	Strongly suffixing
130	26	Weakly suffixing
131	26	Equal prefixing and suffixing
132	26	Weakly prefixing
133	26	Strong prefixing
134	27	Productive full and partial reduplication
135	27	Full reduplication only
136	27	No productive reduplication
137	28	No case marking
138	28	Core cases only
139	28	Core and non-core
140	28	No syncretism
141	29	No subject person/number marking
142	29	Syncretic
143	29	Not syncretic
\.


--
-- Data for Name: cals_language; Type: TABLE DATA; Schema: public; Owner: cals
--

COPY "cals_language" (id, name, author_id, homepage, greeting) FROM stdin;
1	Taruven	\N	\N	\N
\.


--
-- Data for Name: cals_language_features; Type: TABLE DATA; Schema: public; Owner: cals
--

COPY "cals_language_features" (id, language_id, featurevalue_id) FROM stdin;
1	1	3
2	1	17
3	1	11
4	1	19
5	1	7
\.


--
-- Data for Name: auth_group; Type: TABLE DATA; Schema: public; Owner: cals
--

COPY auth_group (id, name) FROM stdin;
\.


--
-- Data for Name: auth_group_permissions; Type: TABLE DATA; Schema: public; Owner: cals
--

COPY auth_group_permissions (id, group_id, permission_id) FROM stdin;
\.


--
-- Data for Name: auth_message; Type: TABLE DATA; Schema: public; Owner: cals
--

COPY auth_message (id, user_id, message) FROM stdin;
\.


--
-- Data for Name: auth_permission; Type: TABLE DATA; Schema: public; Owner: cals
--

COPY auth_permission (id, name, content_type_id, codename) FROM stdin;
34	Can add language	12	add_language
35	Can change language	12	change_language
36	Can delete language	12	delete_language
13	Can add content type	5	add_contenttype
14	Can change content type	5	change_contenttype
15	Can delete content type	5	delete_contenttype
28	Can add feature	10	add_feature
29	Can change feature	10	change_feature
30	Can delete feature	10	delete_feature
25	Can add feature value	9	add_featurevalue
26	Can change feature value	9	change_featurevalue
27	Can delete feature value	9	delete_featurevalue
4	Can add group	2	add_group
5	Can change group	2	change_group
6	Can delete group	2	delete_group
31	Can add language	11	add_language
32	Can change language	11	change_language
33	Can delete language	11	delete_language
22	Can add log entry	8	add_logentry
23	Can change log entry	8	change_logentry
24	Can delete log entry	8	delete_logentry
1	Can add message	1	add_message
2	Can change message	1	change_message
3	Can delete message	1	delete_message
10	Can add permission	4	add_permission
11	Can change permission	4	change_permission
12	Can delete permission	4	delete_permission
16	Can add session	6	add_session
17	Can change session	6	change_session
18	Can delete session	6	delete_session
19	Can add site	7	add_site
20	Can change site	7	change_site
21	Can delete site	7	delete_site
7	Can add user	3	add_user
8	Can change user	3	change_user
9	Can delete user	3	delete_user
\.


--
-- Data for Name: auth_user; Type: TABLE DATA; Schema: public; Owner: cals
--

COPY auth_user (id, username, first_name, last_name, email, password, is_staff, is_active, is_superuser, last_login, date_joined) FROM stdin;
1	admin			kaleissin@gmail.com	sha1$40dd1$2f03c88383d8575abc6c9b1f12a224a80e0708d4	t	t	t	2008-04-27 17:06:33+02	2008-04-27 17:06:06+02
\.


--
-- Data for Name: auth_user_groups; Type: TABLE DATA; Schema: public; Owner: cals
--

COPY auth_user_groups (id, user_id, group_id) FROM stdin;
\.


--
-- Data for Name: auth_user_user_permissions; Type: TABLE DATA; Schema: public; Owner: cals
--

COPY auth_user_user_permissions (id, user_id, permission_id) FROM stdin;
\.


--
-- Data for Name: django_admin_log; Type: TABLE DATA; Schema: public; Owner: cals
--

COPY django_admin_log (id, action_time, user_id, content_type_id, object_id, object_repr, action_flag, change_message) FROM stdin;
\.


--
-- Data for Name: django_content_type; Type: TABLE DATA; Schema: public; Owner: cals
--

COPY django_content_type (id, name, app_label, model) FROM stdin;
1	message	auth	message
2	group	auth	group
3	user	auth	user
4	permission	auth	permission
5	content type	contenttypes	contenttype
6	session	sessions	session
7	site	sites	site
8	log entry	admin	logentry
9	category	cals	category
10	feature value	cals	featurevalue
11	feature	cals	feature
12	language	cals	language
\.


--
-- Data for Name: django_session; Type: TABLE DATA; Schema: public; Owner: cals
--

COPY django_session (session_key, session_data, expire_date) FROM stdin;
\.


--
-- Data for Name: django_site; Type: TABLE DATA; Schema: public; Owner: cals
--

COPY django_site (id, domain, name) FROM stdin;
1	example.com	example.com
\.


--
-- PostgreSQL database dump complete
--

