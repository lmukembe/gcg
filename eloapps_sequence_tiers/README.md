Les comptes auxiliaires clients (411000 Clients) et fournisseurs (401000 Fournisseurs de biens et services) sont bien souvent subdivisés afin de permettre d'assurer un meilleur suivi comptable des factures et des paiements
Mais une alternative sur odoo est possible avec un champ <Compte tier> qui permet d'assigner automatiquement une séquence ( 411xxx pour les clients et 401xxx pour les fournisseurs) sans compliquer le plan comptable avec des comptes tiers pour chacuns de ces partenaires

Sur le formulaire des contacts <res.partner> :
    Dans l’onglet <Facturation>, un champ <Compte tier>, de type caractère, sous le champ <Compte Fournisseur> (modifiable, unique, obligatoire)
        Le champ <Compte tier> est remplit après une modification (sauvegarde, et pas à la création) comme suit :
            Si le champ <Est un client> est vrai, prend la séquence <Comptes clients>
            Si le champ <Est un fournisseur> est vrai, prend la séquence <Comptes fournisseurs>
            Si le champ <Est un client> et  <Est un fournisseur> sont vrai, prend la séquence <Comptes clients>
            Si le champ est déjà rempli, la valeur existante n'est pas ecrasé
        le nom du client est concaténé avec le champ <Compte tier> comme suit : [<Compte tier>] <Nom> sur le champ <display_name> 