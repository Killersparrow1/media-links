/**
 * Media Link Manager - Google Apps Script Backend
 *
 * Deploy as Web App:
 *   Deploy > New deployment > Web app
 *   Description: Media Link Manager API
 *   Execute as: Me
 *   Who has access: Anyone
 */

const SHEET_NAME = 'MediaLinks';
const HEADERS = [
  'ID','Title','Year','Resolution','File Size','Codec',
  'Audio Codec','Source','Download URL','TMDB ID','Poster URL',
  'Overview','Genre','Rating','Date Added','Watched','Notes',
  'Type','Season','Episode'
];

function getSheet_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
    sheet.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]);
    sheet.setFrozenRows(1);
    sheet.getRange('1:1').setFontWeight('bold');
  } else {
    const existingHeaders = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0].map(h => String(h).trim());
    if (existingHeaders.length < HEADERS.length) {
      const newHeaders = [];
      for (let i = existingHeaders.length; i < HEADERS.length; i++) {
        newHeaders.push(HEADERS[i]);
      }
      if (newHeaders.length > 0) {
        sheet.getRange(1, existingHeaders.length + 1, 1, newHeaders.length).setValues([newHeaders]);
        sheet.getRange('1:1').setFontWeight('bold');
      }
    }
  }
  return sheet;
}

function doGet(e) {
  const action = e?.parameter?.action || 'getAll';

  try {
    const sheet = getSheet_();
    const data = sheet.getDataRange().getValues();
    const rows = dataToObjects_(data);

    let result;
    switch (action) {
      case 'getAll':
        result = { success: true, data: rows };
        break;

      case 'search': {
        const q = (e?.parameter?.q || '').toLowerCase();
        result = {
          success: true,
          data: rows.filter(r =>
            (r.Title || '').toLowerCase().includes(q) ||
            (r.Overview || '').toLowerCase().includes(q)
          )
        };
        break;
      }

      case 'delete': {
        const id = e?.parameter?.id;
        if (!id) throw new Error('Missing id parameter');
        const rowIndex = rows.findIndex(r => r.ID === id);
        if (rowIndex === -1) throw new Error('Link not found');
        sheet.deleteRow(rowIndex + 2); // +2 for header + 1-based
        result = { success: true, message: 'Deleted' };
        break;
      }

      default:
        result = { success: false, error: 'Unknown action: ' + action };
    }

    return output_(result);

  } catch (err) {
    return output_({ success: false, error: err.message });
  }
}

function doPost(e) {
  try {
    const data = JSON.parse(e?.postData?.contents || '{}');
    if (!data.title || !data.url) {
      return output_({ success: false, error: 'Title and URL are required' });
    }

    const sheet = getSheet_();
    const row = [
      data.id || Date.now().toString(),
      data.title,
      data.year || '',
      data.resolution || '',
      data.size || '',
      data.codec || '',
      data.audio || '',
      data.source || '',
      data.url,
      data.tmdbId || '',
      data.poster || '',
      data.overview || '',
      data.genre || '',
      data.rating || '',
      data.dateAdded || new Date().toISOString(),
      data.watched || 'No',
      data.notes || '',
      data.type || '',
      data.season || '',
      data.episode || ''
    ];
    sheet.appendRow(row);

    return output_({ success: true, message: 'Link added' });

  } catch (err) {
    return output_({ success: false, error: err.message });
  }
}

function dataToObjects_(data) {
  if (data.length < 2) return [];
  const headers = data[0].map(h => String(h).trim());
  const objects = [];
  for (let i = 1; i < data.length; i++) {
    const obj = {};
    for (let j = 0; j < headers.length; j++) {
      obj[headers[j]] = data[i][j];
    }
    objects.push(obj);
  }
  return objects;
}

function output_(payload) {
  return ContentService
    .createTextOutput(JSON.stringify(payload))
    .setMimeType(ContentService.MimeType.JSON);
}
