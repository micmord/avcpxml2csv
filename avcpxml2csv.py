#!/bin/python

# avcpxml2csv is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# avcpxml2csv is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with avcpxml2csv.  If not, see <http://www.gnu.org/licenses/>.

'''
Semplice programma per la conversione del file XML aderente alle specifiche
tecniche di AVCP in ottemperanza a Art.1,comma 32,L.190/2012.

Specifiche XML:
 * http://dati.avcp.it/schema/datasetAppaltiL190.xsd
 * http://dati.avcp.it/schema/TypesL190.xsd

Tested with Python 2.7

@author: Michele Mordenti
@version: 0.2-dev
'''

import sys
import xml.etree.ElementTree as ET
import codecs
import re

# PARAMETRI
CODIFICA_XML_SORGENTE='utf-8'
DELIMITER=';'
QUOTECHAR='"'
ESCAPE="'"
ND = 'n/d'


# Leggo argomenti
if len(sys.argv)!=2 :
    print ('Specificare il nome del file contenete il tracciato record XML di AVCP')
    print ('Esempio: ' + sys.argv[0] + 'avcp_dataset_2013.xml')
    sys.exit(1)

XML_INPUT=sys.argv[1]

try:
    tree = ET.parse(XML_INPUT)
    foutput = codecs.open(XML_INPUT + '.csv', 'w', encoding=CODIFICA_XML_SORGENTE)
except IOError:
    print ('Non posso aprire il file' + XML_INPUT)
    sys.exit(2)


def convertiData(data):
  '''Banale funzione di conversione della data
     input: None --> output: ND
     input: "aaaa-mm-gg" --> output: "gg/mm/aaaa"
     input: "aaaa-mm-gg+hh:mm" --> output: "gg/mm/aaaa (+hh:mm)"
     input: * --> output *
  '''
  if (data is not None):
    if (re.match('^\d{4}-\d{2}-\d{2}$',data) is not None):
      p = re.compile('(\d+)-(\d+)-(\d+)')
      return (p.match(data).group(3) + '/' +
             p.match(data).group(2) + '/' +
             p.match(data).group(1))
    if (re.match('^\d{4}-\d{2}-\d{2}\+\d{2}:\d{2}$',data) is not None):
      p = re.compile('(\d+)-(\d+)-(\d+)\+(\d+:\d+)')
      return (p.match(data).group(3) + '/' +
             p.match(data).group(2) + '/' +
             p.match(data).group(1) + ' (+' +
             p.match(data).group(4) + ')')
    return data
  return ND

# Radice del tracciato XML
root = tree.getroot()

# Heder CSV
foutput.write(QUOTECHAR + 'CIG' + QUOTECHAR + DELIMITER +
              QUOTECHAR + 'Proponente' + QUOTECHAR + DELIMITER +
              QUOTECHAR + 'Codice Fiscale' + QUOTECHAR + DELIMITER +
              QUOTECHAR + 'Oggetto' + QUOTECHAR + DELIMITER +
              QUOTECHAR + 'Scelta contraente' + QUOTECHAR + DELIMITER +
              QUOTECHAR + 'Ditta partecipante' + QUOTECHAR + DELIMITER +
              QUOTECHAR + 'Codice Fiscale' + QUOTECHAR + DELIMITER +
              QUOTECHAR + 'ITA' + QUOTECHAR + DELIMITER +
              QUOTECHAR + 'Raggruppamento' + QUOTECHAR + DELIMITER +
              QUOTECHAR + 'Ruolo' + QUOTECHAR + DELIMITER +
              QUOTECHAR + 'Aggiudicatario' + QUOTECHAR + DELIMITER +
              QUOTECHAR + 'Importo' + QUOTECHAR + DELIMITER +
              QUOTECHAR + 'Data inizio' + QUOTECHAR + DELIMITER +
              QUOTECHAR + 'Data fine' + QUOTECHAR + DELIMITER +
              QUOTECHAR + 'Liquidato' + QUOTECHAR + DELIMITER + '\n')

lotti = root.find('data')
# Ciclo principale su tutti i lotti
for lotto in lotti.iter('lotto'):
  headerRow = QUOTECHAR + lotto.find('cig').text + QUOTECHAR + DELIMITER
  headerRow += QUOTECHAR + lotto.find('strutturaProponente').find('denominazione').text + QUOTECHAR + DELIMITER
  headerRow += QUOTECHAR + lotto.find('strutturaProponente').find('codiceFiscaleProp').text + QUOTECHAR + DELIMITER
  headerRow += QUOTECHAR + lotto.find('oggetto').text.replace(QUOTECHAR,ESCAPE) + QUOTECHAR + DELIMITER
  headerRow += QUOTECHAR + lotto.find('sceltaContraente').text + QUOTECHAR + DELIMITER
  tailerRow = QUOTECHAR + lotto.find('importoAggiudicazione').text + QUOTECHAR + DELIMITER  
  inizio = lotto.find('tempiCompletamento').find('dataInizio')
  fine = lotto.find('tempiCompletamento').find('dataUltimazione')
  if ( inizio is not None):
    dataInizio = convertiData(inizio.text)
  else:
    dataInizio = 'n/d'
  if (fine is not None):
    dataFine = convertiData(fine.text)
  else:
    dataFine = 'n/d'
  tailerRow += QUOTECHAR + dataInizio + QUOTECHAR + DELIMITER
  tailerRow += QUOTECHAR + dataFine + QUOTECHAR + DELIMITER
  tailerRow += QUOTECHAR + lotto.find('importoSommeLiquidate').text + QUOTECHAR + '\n'

  # lista vincitori
  listaAggiudicatari = []
  aggiudicatari=lotto.find('aggiudicatari')
  for aggiudicatario in aggiudicatari.iter('aggiudicatario'):
    if (aggiudicatario.find('codiceFiscale') is not None):
      cf = aggiudicatario.find('codiceFiscale').text
    else:
      cf = aggiudicatario.find('identificativoFiscaleEstero').text
    listaAggiudicatari.append(cf)
  for raggruppamento in aggiudicatari.iter('aggiudicatarioRaggruppamento'):
    for membro in raggruppamento.iter('membro'):
      if (membro.find('codiceFiscale') is not None):
        cf = membro.find('codiceFiscale').text
      else:
        cf = membro.find('identificativoFiscaleEstero').text
      listaAggiudicatari.append(cf)
  # partecipanti
  partecipanti=lotto.find('partecipanti')
  # se presenti li scrivo
  if ((partecipanti.find('partecipante') is not None) or (partecipanti.find('raggruppamento') is not None)):  
    for partecipante in partecipanti.iter('partecipante'):
      row = headerRow + QUOTECHAR + partecipante.find('ragioneSociale').text.replace(QUOTECHAR,ESCAPE) + QUOTECHAR + DELIMITER
      if (partecipante.find('codiceFiscale') is not None):
        cf = partecipante.find('codiceFiscale').text
        row += QUOTECHAR + cf + QUOTECHAR + DELIMITER
        row += QUOTECHAR + 'SI' + QUOTECHAR + DELIMITER
      else:
        cf = partecipante.find('identificativoFiscaleEstero').text
        row += QUOTECHAR + cf + QUOTECHAR + DELIMITER
        row += QUOTECHAR + 'NO' + QUOTECHAR + DELIMITER
      row += QUOTECHAR + 'NO' + QUOTECHAR + DELIMITER # raggruppamento
      row += QUOTECHAR + 'singolo' + QUOTECHAR + DELIMITER # ruolo
      if cf in listaAggiudicatari:
        row += QUOTECHAR + 'SI' + QUOTECHAR + DELIMITER
      else:
        row += QUOTECHAR + 'NO' + QUOTECHAR + DELIMITER
      # scrivo
      foutput.write(row + tailerRow)
    # Raggruppamenti
    r = 0
    for raggruppamento in partecipanti.iter('raggruppamento'):
      r += 1 
      for membro in raggruppamento.iter('membro'):
        row = headerRow + QUOTECHAR + membro.find('ragioneSociale').text.replace(QUOTECHAR,ESCAPE) + QUOTECHAR + DELIMITER
        if (membro.find('codiceFiscale') is not None):
          cf = membro.find('codiceFiscale').text
          row += QUOTECHAR + cf + QUOTECHAR + DELIMITER
          row += QUOTECHAR + 'SI' + QUOTECHAR + DELIMITER    
        else:
          cf = membro.find('identificativoFiscaleEstero').text
          row += QUOTECHAR + cf + QUOTECHAR + DELIMITER
          row += QUOTECHAR + 'NO' + QUOTECHAR + DELIMITER
        row += QUOTECHAR + 'R' + str(r) + QUOTECHAR + DELIMITER # raggruppamento
        row += QUOTECHAR + membro.find('ruolo').text + QUOTECHAR + DELIMITER # ruolo
        if cf in listaAggiudicatari:
          row += QUOTECHAR + 'SI' + QUOTECHAR + DELIMITER
        else:
          row += QUOTECHAR + 'NO' + QUOTECHAR + DELIMITER
        # scrivo
        foutput.write(row + tailerRow)
  else:
    # partecipanti assenti, scrivo solo i dati della gara
    foutput.write(headerRow +
                  QUOTECHAR + QUOTECHAR + DELIMITER +
                  QUOTECHAR + QUOTECHAR + DELIMITER +
                  QUOTECHAR + QUOTECHAR + DELIMITER +
                  QUOTECHAR + QUOTECHAR + DELIMITER +
                  QUOTECHAR + QUOTECHAR + DELIMITER +
                  QUOTECHAR + QUOTECHAR + DELIMITER +
                  tailerRow)
foutput.close()
