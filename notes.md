### interface for scoring rule
#### goal: test out rules for scoring, what's in wordbank.  
- it insults, you insult
- better wordbank? e.g., color by pos
- difficulty
    + random sampler, max over increasing set
- accelerate input, matching + bar



### interface for limit break, "fucking"
- options for showing p.o.s., etc
- allow all words, subsets

logging

hypernym viewer (one word or pair of words)
- links to root
- links to each other
- each item links to wordnet entry

sanity check grammar, 
filter repetition (alliteration), 
generate similar phrase, 
score similarity between words, 


phrase trees?

comparative voice?


You bourgeois warmonger, your accusation against the DPRK is no more than barking at the moon! -- KCNA

complete phrase Brigandish ???

1. identify high level synset?
2. collect hyponyms, filter
Motley Assembly Of Self-Righteous Bottomfeeders
Assembly => social group
social group => ~100 hyponyms
might set boundaries of what's usable, or just give bonus, still apply bonuses between eg adj and noun
longer insult phrase as limmit break
in general, conjugations or lists could have a lower average effect but allow for chaining bonuses


Bedecked In Cloaca -- how to expand bedecked in, coated in, covered in? verb past participles with matching sense + usage of in? look for trigrams seeded on "coated in shit" => "____ in shit" ==> "___ in cloaca"
google n gram is a good place to start for n grams

 Motley Assembly Of Self-Righteous Bottomfeeders -- assembly fits a known wordnet hierarchy

 A Hierarchy Of Technocrats And Underlings --  
 Writhing Mass Of Auto-Fellatio

 A Clubhouse Of Half-Awake Self-Opinionated, Monomaniac Louts

 Satin-Coated Racketeers Of Theocratic Blackmail -- ??? how to sort prepositional phrases??

 An Aberration Chartered In Sin

 A Gloomy Temple Consecrated To Lust And Error





design

front-end
- master divs
- 


back-end
- word2vec other databases -- blackwood's, urbandictionary, wiki, 
- WordNet.lemmatize not as good as web search (men, errand boys)
- get wordnet understanding and python interface up to speed
- augmented wordnet (stanford)
- web matching: unelected yahoo => https://ryanjonsyrek.wordpress.com/2014/06/02/tilting-at-windmills-in-a-state-that-has-too-few-of-them/

embeddings
- find more pre-trained, https://www.quora.com/Where-can-I-find-some-pre-trained-word-vectors-for-natural-language-processing-understanding
- alternate word2vec
- continuous bag of words

http://corpus.byu.edu/full-text/ historical, contemporary, global corpora

british library sounds

comparative table of simple adj/noun pairs (JJ NN)
	- in synnet, GN w2v?
	- clustering
	- http://irsrv2.cs.biu.ac.il:9998/?word=sycophant

special use items: fucking
redo conversation

dojo w/ hammer scale or regular scale 
e.g., learn not to pair dumb stuff "treasonous traitor"
where do your vulnerabilities come from?
spiritual successor to reader rabbit
ATM to buy words
typing game to get words
text to speech challenge to get words

faithlife corp: https://www.logos.com/
premature balding and ectopic organs


PENN tags
1.	CC	Coordinating conjunction
2.	CD	Cardinal number
3.	DT	Determiner
4.	EX	Existential there
5.	FW	Foreign word
6.	IN	Preposition or subordinating conjunction
7.	JJ	Adjective
8.	JJR	Adjective, comparative
9.	JJS	Adjective, superlative
10.	LS	List item marker
11.	MD	Modal
12.	NN	Noun, singular or mass
13.	NNS	Noun, plural
14.	NNP	Proper noun, singular
15.	NNPS	Proper noun, plural
16.	PDT	Predeterminer
17.	POS	Possessive ending
18.	PRP	Personal pronoun
19.	PRP$	Possessive pronoun
20.	RB	Adverb
21.	RBR	Adverb, comparative
22.	RBS	Adverb, superlative
23.	RP	Particle
24.	SYM	Symbol
25.	TO	to
26.	UH	Interjection
27.	VB	Verb, base form
28.	VBD	Verb, past tense
29.	VBG	Verb, gerund or present participle
30.	VBN	Verb, past participle
31.	VBP	Verb, non-3rd person singular present
32.	VBZ	Verb, 3rd person singular present
33.	WDT	Wh-determiner
34.	WP	Wh-pronoun
35.	WP$	Possessive wh-pronoun
36.	WRB	Wh-adverb

word2vec
http://streamhacker.com/2014/12/29/word2vec-nltk/

https://wordnet.princeton.edu/

http://www.nltk.org/book/ch02.html
http://www.nltk.org/book/ch05.html

mad cavern, robots instructed by foul-mouthed mechanic from north new jersey
more tropes

fractal maps, hidden object
https://en.wikipedia.org/wiki/Dragon_curve
