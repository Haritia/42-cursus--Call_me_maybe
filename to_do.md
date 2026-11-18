Voici le sujet décortiqué de bout en bout, en mode mentor : je t'explique, je t'oriente, et je te laisse écrire le code. C'est toi qui devras le défendre en évaluation.

---

## 1. Ce qu'on te demande vraiment

En surface, il faut un programme qui lit des questions en langage naturel (« What is the sum of 2 and 3? ») et une liste de fonctions disponibles. Pour chaque question, il écrit dans un fichier JSON quelle fonction appeler et avec quels arguments typés :

```json
{"prompt": "What is the sum of 2 and 3?", "name": "fn_add_numbers", "parameters": {"a": 2.0, "b": 3.0}}
```

Le vrai sujet est ailleurs. On te donne un modèle minuscule (Qwen3-0.6B) qui, livré à lui-même, ne produit du JSON correct qu'environ 30 % du temps. Tu dois le faire passer à 100 % de JSON valide et 90 % ou plus de bonnes réponses. Pour ça, tu n'as pas le droit d'améliorer le modèle ni d'utiliser une bibliothèque qui le fait à ta place (pas d'outlines, de transformers ou de torch). Tu n'as droit qu'à trois choses :
- les **logits**, c'est-à-dire le score que le modèle donne à chaque token possible pour la suite ;
- le **vocabulaire**, la correspondance entre l'id d'un token et son texte ;
- ta **logique**, pour décider quels tokens sont autorisés à chaque étape.

Tu ne codes donc pas un agent, tu codes le **décodeur** : la boucle qui choisit les tokens un par un. Le modèle propose, ton code décide.

Trois contraintes cachées comptent beaucoup :
1. **C'est le LLM qui choisit la fonction.** Pas de `if "sum" in prompt`, c'est la « medieval magic » interdite par le sujet.
2. **Pas de hardcode.** Les fichiers d'entrée changent pendant l'évaluation.
3. **Moins de 5 minutes pour tout traiter.** Or chaque appel à `get_logits_from_input_ids` fait passer toute la séquence dans le réseau. Le nombre d'appels au modèle est donc ton budget principal.

## 2. L'analogie

Imagine un stagiaire brillant mais distrait, à qui tu demandes de remplir un formulaire administratif. Si tu lui donnes une feuille blanche, il écrit des phrases, oublie des champs, met « deux » au lieu de « 2 ». Si tu lui donnes un vrai formulaire, tout change :
- les **cases et les intitulés sont déjà imprimés** : il n'écrit pas `"name":`, c'est déjà sur la feuille ;
- le **nom de la fonction est un menu déroulant** : il ne peut choisir que parmi les options existantes ;
- la **case « nombre » n'accepte que des chiffres**, un signe moins et un point ;
- la **case « texte » accepte tout**, sauf le guillemet qui la fermerait.

Le stagiaire garde toute son intelligence : c'est lui qui comprend que « 265 et 345 » va dans les cases a et b. Mais il lui est physiquement impossible de produire un formulaire invalide. Le formulaire, c'est ton constrained decoding.

## 3. Mind map des solutions

Le problème se découpe en quatre sous-problèmes, chacun avec plusieurs pistes possibles. Voici la carte, juste en dessous.

Les quatre idées à retenir de la carte :

- **Squelette forcé.** `{"name": "`, puis `", "parameters": {"a": `, etc. sont connus d'avance. Tu ajoutes directement ces tokens à la séquence, **sans demander son avis au modèle**. Le LLM ne travaille qu'aux « points de décision » : le nom de la fonction et les valeurs. Résultat : moins d'appels au modèle, donc plus de vitesse, et aucune chance de casser la structure. Les clés des paramètres viennent du schéma de la fonction choisie.
- **Trie des noms.** À chaque étape du nom, un token n'est autorisé que si « ce qui est déjà généré + ce token » reste le début d'au moins un nom valide. C'est le LLM qui choisit, mais seulement parmi des chemins qui existent. L'alternative (calculer le score de chaque nom complet et prendre le meilleur) est valable aussi. Garde-la en tête pour comparer la précision.
- **Une FSM par type.** `number` accepte `-?\d+(\.\d+)?`, `string` accepte tout sauf `"` non échappé, `boolean` accepte `true` ou `false`. Chaque type est un petit automate qui répond à deux questions : « ce texte est-il encore un début valide ? » et « est-ce que je peux m'arrêter ici ? ».
- **Masques pré-calculés.** Le vocabulaire de Qwen compte environ 151 000 tokens. Les tester un par un en Python à chaque étape tuerait ton budget de 5 minutes. Tu décodes donc tout le vocabulaire **une seule fois** au démarrage, puis tu prépares des tableaux numpy (« tokens qui ne sont que des chiffres », « tokens sans guillemet »…). À chaque étape, il ne reste qu'à appliquer le bon masque.

Deux pièges à connaître dès maintenant :
- Le fichier de vocabulaire est en **byte-level BPE** : `Ġ` veut dire espace, `Ċ` veut dire saut de ligne. Il faut retraduire chaque token vers son vrai texte, sinon tes filtres seront faux.
- Qwen3 est un modèle qui « réfléchit ». Avec son format de chat (`<|im_start|>`…), pense à fermer tout de suite le bloc `<think>` vide, pour qu'il ne parte pas en raisonnement.

## 4. Roadmap

Chaque phase se termine par un livrable qui fonctionne et que tu peux tester.

| Phase | Tâches concrètes | C'est fini quand… |
|---|---|---|
| **0. Setup** | `uv init`, `pyproject.toml` avec numpy et pydantic, copier `llm_sdk/`, Makefile (install, run, debug, clean, lint), `.gitignore`, arborescence `src/` | `make lint` passe sur un `__main__.py` vide, et `uv sync` installe tout |
| **1. Labo tokenizer** | Script jetable : charger le modèle, encoder un prompt, ouvrir le fichier de vocabulaire, chronométrer un appel aux logits, faire une boucle gloutonne de 30 tokens **sans contrainte** | Tu sais expliquer `Ġ`, la taille du vocabulaire, le temps d'un appel, et tu as vu le modèle rater son JSON |
| **2. I/O et modèles** | Modèles pydantic (`FunctionDefinition`, `PromptItem`, `FunctionCallResult`), CLI avec argparse, gestion des fichiers absents et du JSON invalide | Le programme écrit un fichier de sortie factice, ne crashe jamais, et affiche des erreurs claires |
| **3. Vocabulaire** | Classe `Vocabulary` : id vers texte décodé (bytes vers unicode), tableaux numpy par classe de tokens | Décoder une séquence avec ta classe donne le même texte que `decode()` du SDK |
| **4. Choix de fonction** | Prompt système, squelette forcé jusqu'au nom, trie des noms, sélection contrainte | Plus de 90 % de noms corrects sur les tests fournis |
| **5. Arguments** | Contraintes number, integer, string, boolean, injection des clés, détection de fin de valeur | Sortie complète, 100 % parsable, types conformes |
| **6. Évaluation** | Script qui mesure la précision et le temps, jeu de tests à toi (prompts piégeux, nombres négatifs, guillemets dans les chaînes) | Tableau de chiffres pour le README, moins de 5 minutes |
| **7. Finitions** | pytest, `lint-strict`, README complet en anglais, bonus éventuels (propre `encode`, visualisation) | Tu peux défendre chaque ligne et modifier le code en direct en 5 minutes |

## 5. Design patterns

Fixe-toi ce chemin et ne le quitte plus :

- **Architecture en pipeline.** `Loader → PromptBuilder → FunctionSelector → ArgumentGenerator → Writer`. Chaque étape a une entrée et une sortie typées en pydantic, et se teste toute seule.
- **Strategy pour les contraintes.** C'est le cœur du projet. Une interface abstraite `Constraint` avec trois méthodes : `allowed_mask(prefix) -> np.ndarray`, `is_complete(prefix) -> bool` et `can_continue(prefix) -> bool`. Puis une classe par type : `ChoiceConstraint` (noms de fonctions), `NumberConstraint`, `StringConstraint`, `BooleanConstraint`. Ajouter un type plus tard, `integer` ou un objet imbriqué pour le bonus, revient à ajouter une classe sans toucher au reste. C'est exactement le genre de modification qu'on peut te demander en soutenance.
- **State machine (FSM).** C'est l'implémentation interne de chaque contrainte, et le concept que le correcteur voudra t'entendre expliquer.
- **Facade (Adapter) sur le SDK.** Une classe `LLMClient` qui enveloppe `Small_LLM_Model`. Le reste du code ne parle qu'à elle, ce qui te permet de la remplacer par un faux modèle dans les tests, sans charger 600M de paramètres.
- **Un seul moteur de décodage.** `ConstrainedDecoder.generate(prefix_ids, constraint) -> str` : la même boucle sert pour le nom et pour tous les arguments. Sans ça, tu vas copier-coller la boucle de génération trois fois.

Arborescence cible :
```
src/
  __main__.py        # CLI, orchestration, gestion d'erreurs globale
  models.py          # schémas pydantic
  io_utils.py        # lecture/écriture JSON robuste
  llm_client.py      # facade sur llm_sdk
  vocabulary.py      # décodage du vocab, masques
  prompt_builder.py  # template de chat Qwen
  decoder.py         # boucle de génération contrainte
  constraints/       # base.py, choice.py, number.py, string.py, boolean.py
  function_caller.py # nom puis arguments
```

## 6. La première étape : le labo tokenizer (phase 0, puis 1)

Ne code rien de « propre » tout de suite. Ce qui bloquera toute la suite, c'est de ne pas comprendre concrètement ce qui circule entre toi et le modèle. Fais d'abord le setup (un `uv sync` et un `make lint` qui passent), puis écris un script jetable `lab.py` qui répond à ces questions :

1. Combien de tokens donne `encode("What is the sum of 2 and 3?")` ? Quels sont leurs ids, et quel type d'objet est renvoyé (un tenseur, à convertir en liste) ?
2. Ouvre le fichier donné par `get_path_to_vocab_file()`. Quelle est sa structure, texte vers id ou l'inverse ? Combien d'entrées ? Trouve trois tokens contenant `Ġ` et trois contenant un `"`.
3. Combien de valeurs renvoie `get_logits_from_input_ids()` ? Combien de temps prend un appel avec 50 tokens, puis avec 300 ? Ça te donnera ton budget d'appels pour les 5 minutes.
4. Écris une boucle gloutonne de 30 itérations : prendre les logits, faire `argmax`, ajouter le token, recommencer. Donne-lui un prompt qui demande du JSON. Qu'est-ce qui sort ? Garde ce résultat, c'est ta preuve « avant » pour le README.

Reviens avec tes réponses (chiffres et observations). On les analysera ensemble, puis on attaquera la classe `Vocabulary` et le premier masque. Si tu bloques sur un point du labo, dis-moi lequel et je te guide sans te donner la solution toute faite.

Tu veux que je mette ce plan sur un Whiteboard ?

```
Tu es mon mentor, avec le contexte joint, c'est le sujet que je vais traite, tu vas m'aide a bien structure le projet, et a plannifier, resoudre et perfectionner le resultat.
commemceons par la comprehension du sujet

- qu'est ce qui nous est demande de faire dans le sujet
- provide une analogie de la demande
- commanceons par le mind mapping des solutions possible pour arrive a la satisfactions des contrainte
- quel est le road map a suivre, pour bien structure le travail, terminer des partie utile a la marche ers la solution, des taches concrete
- design pattern du projet, pour se fixer dans un chemin precis
-quel est donc la premiere etape
```