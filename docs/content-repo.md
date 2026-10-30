# Content-repo
De content-repo is [hay/siboga-content](https://github.com/hay/siboga-content): een Obsidian-kluis met markdownbestanden. Het is het redactiesysteem van de site en de *source of truth*. Meerdere mensen schrijven erin.

De code-repo gebruikt de content-repo alleen als bron. De pipeline leest hem en schrijft er nooit in. Alles wat met techniek te maken heeft, staat in de code-repo.

## Hoe de content binnenkomt
- Redacteuren schrijven in Obsidian. De community-plugin **Fit** synchroniseert de kluis met GitHub.
- Voor de pipeline is het gewoon een git-repo. Lokaal staat een kloon in `content/` in de code-repo (niet in git). Het pad is in te stellen in `pipeline/config.toml`, zodat je ook naar een andere map kunt wijzen, zoals je eigen Obsidian-kluis.

## Mappen
| Map of bestand | Inhoud |
|---|---|
| `chapters/` | Hoofdstukken van het verhaal (`type: chapter`) |
| `records/` | Records: personen, voorwerpen, plekken, media enzovoort (`type: record`) |
| `.obsidian/` | Instellingen van Obsidian; de pipeline negeert dit |
| `README.md`, `Welkom.md`, `Welcome.md` | Geen content; de pipeline slaat ze over omdat ze geen `type` hebben |

De pipeline kijkt naar het veld `type` in de frontmatter, niet naar de map. Een bestand zonder `type` wordt overgeslagen. Zo maakt het niet uit als een redacteur een bestand in de verkeerde map zet.

## Frontmatter
Stand van 2026-10-30, afgeleid uit de bestanden die er nu staan. Dit wordt aangevuld zodra het formaat vastligt.

### Record
```yaml
---
type: record
uri: https://www.wikidata.org/wiki/Q1940785
description_nl: Nederlands wierendeskundige
contenttype: person
---
```

| Veld | Verplicht | Betekenis |
|---|---|---|
| `type` | ja | Altijd `record` |
| `uri` | ja | Verwijzing naar de bron. Nu één URL; de pipeline accepteert ook een lijst, zodat een record meerdere bronnen kan hebben |
| `description_nl` | nee | Korte Nederlandse beschrijving. Heeft voorrang op de beschrijving uit de bron |
| `contenttype` | ja | Soort record, zie hieronder |

Waarden van `contenttype` die nu voorkomen: `person`, `item`, `media`, `location`, `article`, `expedition`, `specimen`.

Bronnen die nu voorkomen in `uri`: Wikidata (`wikidata.org/wiki/Q…`), Stadsarchief Amsterdam (`beta.archief.amsterdam/detail/…`), Delpher en GBIF (`gbif.org/taxon/…`).

### Chapter
```yaml
---
type: chapter
chapter: "1"
location: "[[Haven Jakarta]]"
---
```

| Veld | Verplicht | Betekenis |
|---|---|---|
| `type` | ja | Altijd `chapter` |
| `chapter` | ja | Volgnummer, als tekst |
| `location` | nee | Wikilink naar een record met `contenttype: location` |

De titel van een record of chapter is de bestandsnaam zonder `.md`.

## Tekst: Obsidian-markdown
De content-repo wordt in Obsidian gelezen en geschreven, niet op GitHub. De tekst is dus Obsidian-markdown: gewone markdown plus een aantal eigen schrijfwijzen. Redacteuren gebruiken die door elkaar, dus de pipeline moet ze allemaal herkennen.

| Schrijfwijze | Voorbeeld | Wat de pipeline doet |
|---|---|---|
| Wikilink | `[[Anna Weber]]` | Link naar het record, met de bestandsnaam als tekst |
| Wikilink met eigen tekst | `[[Weberolegra weberi\|vlinder]]` | Link naar het record, met "vlinder" als tekst |
| Wikilink naar een kop | `[[Anna Weber#Jeugd]]` | Link naar het record; de kop wordt voorlopig genegeerd |
| Wikilink met pad | `[[records/Anna Weber]]` | Zelfde als zonder pad |
| Embed van een bestand | `![[foto anna.jpg]]` of `![[foto anna.jpg\|300]]` | Bestand naar `media/`, in de HTML een `<img>` (of `<audio>`, `<video>`) |
| Embed van een notitie | `![[Anna Weber]]` | Voorlopig behandelen als een gewone wikilink |
| Gewone markdownlink | `[168 publicaties](https://...)` | Blijft een gewone link |
| Markdownlink naar een notitie | `[Anna](records/Anna%20Weber.md)` | Link naar het record, net als een wikilink |
| Wikilink in frontmatter | `location: "[[Haven Jakarta]]"` | Id van het record |
| Commentaar | `%%nog nakijken%%` | Weglaten |
| Callout | `> [!note] Titel` | Een blok met een attribuut als stijlhaak, bijvoorbeeld `<aside callout="note">` |
| Markering | `==belangrijk==` | `<mark>` |
| Tag | `#zoölogie` | Voorlopig weglaten uit de tekst |

Verder:
- Een wikilink verwijst naar een bestandsnaam, niet naar een pad. Obsidian zoekt het bestand in de hele kluis; de pipeline doet dat ook, zonder op hoofdletters te letten.
- Bijlagen (plaatjes, audio, pdf's) kunnen overal in de kluis staan. De pipeline zoekt ze net als notities op bestandsnaam.
- Obsidian gebruikt zachte regeleinden: één enter in de tekst is geen nieuwe alinea. De pipeline volgt dat.

## Wat de pipeline moet verdragen
De content wordt door mensen geschreven en is vaak onaf. In de huidige bestanden komt al voor:
- een leeg bestand zonder frontmatter;
- een `uri` die geen URL is (`wikidata`) of alleen naar de homepage van een dienst wijst (`http://delpher.nl`);
- een wikilink naar een bestand dat (nog) niet bestaat;
- een lege regel in een lijst.

De pipeline crasht hier niet op. Hij slaat het onderdeel over of toont het als gewone tekst, logt een waarschuwing, en geeft aan het eind een overzicht van alle problemen. Dat overzicht is ook nuttig voor de redactie.
