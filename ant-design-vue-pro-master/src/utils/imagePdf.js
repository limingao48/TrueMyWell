const PDF_PAGE_WIDTH = 595.28
const PDF_PAGE_HEIGHT = 841.89

function ensureTextEncoder () {
  if (typeof TextEncoder === 'undefined') {
    throw new Error('当前浏览器不支持 PDF 导出所需的 TextEncoder')
  }
  return new TextEncoder()
}

function encodeText (text) {
  return ensureTextEncoder().encode(text)
}

function partByteLength (part) {
  if (typeof part === 'string') {
    return encodeText(part).length
  }
  return part.length
}

function base64ToBytes (base64) {
  const raw = atob(base64)
  const bytes = new Uint8Array(raw.length)
  for (let i = 0; i < raw.length; i++) {
    bytes[i] = raw.charCodeAt(i)
  }
  return bytes
}

function parseJpegDataUrl (dataUrl) {
  const matched = /^data:image\/jpeg;base64,(.+)$/i.exec(dataUrl || '')
  if (!matched) {
    throw new Error('报告页面必须先渲染为 JPEG 图片后才能导出 PDF')
  }
  return base64ToBytes(matched[1])
}

function formatPdfNumber (value) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return '0'
  return numeric.toFixed(2).replace(/\.?0+$/, '')
}

function calculatePlacement (pixelWidth, pixelHeight) {
  const imageRatio = pixelWidth / pixelHeight
  const pageRatio = PDF_PAGE_WIDTH / PDF_PAGE_HEIGHT

  let drawWidth = PDF_PAGE_WIDTH
  let drawHeight = PDF_PAGE_HEIGHT
  let offsetX = 0
  let offsetY = 0

  if (imageRatio > pageRatio) {
    drawHeight = PDF_PAGE_WIDTH / imageRatio
    offsetY = (PDF_PAGE_HEIGHT - drawHeight) / 2
  } else {
    drawWidth = PDF_PAGE_HEIGHT * imageRatio
    offsetX = (PDF_PAGE_WIDTH - drawWidth) / 2
  }

  return {
    drawWidth,
    drawHeight,
    offsetX,
    offsetY
  }
}

export function createImagePdfFromPages (pages) {
  if (!Array.isArray(pages) || !pages.length) {
    throw new Error('没有可导出的报告页面')
  }

  const normalizedPages = pages.map((page, index) => {
    if (!page || !page.dataUrl || !page.width || !page.height) {
      throw new Error(`第 ${index + 1} 页报告数据不完整`)
    }

    return {
      objectPage: 3 + index * 3,
      objectContent: 4 + index * 3,
      objectImage: 5 + index * 3,
      imageName: `Im${index + 1}`,
      pixelWidth: page.width,
      pixelHeight: page.height,
      imageBytes: parseJpegDataUrl(page.dataUrl),
      placement: calculatePlacement(page.width, page.height)
    }
  })

  const objectCount = 2 + normalizedPages.length * 3
  const offsets = new Array(objectCount + 1).fill(0)
  const parts = []
  let currentOffset = 0

  const pushPart = (part) => {
    parts.push(part)
    currentOffset += partByteLength(part)
  }

  const addObject = (objectNumber, bodyParts) => {
    offsets[objectNumber] = currentOffset
    pushPart(`${objectNumber} 0 obj\n`)
    bodyParts.forEach(pushPart)
    pushPart('\nendobj\n')
  }

  const kids = normalizedPages.map(page => `${page.objectPage} 0 R`).join(' ')

  pushPart('%PDF-1.4\n%\xFF\xFF\xFF\xFF\n')
  addObject(1, ['<< /Type /Catalog /Pages 2 0 R >>'])
  addObject(2, [`<< /Type /Pages /Count ${normalizedPages.length} /Kids [${kids}] >>`])

  normalizedPages.forEach((page) => {
    const placement = page.placement
    const contentStream = [
      'q',
      `${formatPdfNumber(placement.drawWidth)} 0 0 ${formatPdfNumber(placement.drawHeight)} ${formatPdfNumber(placement.offsetX)} ${formatPdfNumber(placement.offsetY)} cm`,
      `/${page.imageName} Do`,
      'Q'
    ].join('\n')
    const contentLength = partByteLength(contentStream)

    addObject(page.objectPage, [
      `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${formatPdfNumber(PDF_PAGE_WIDTH)} ${formatPdfNumber(PDF_PAGE_HEIGHT)}] ` +
      `/Resources << /XObject << /${page.imageName} ${page.objectImage} 0 R >> >> /Contents ${page.objectContent} 0 R >>`
    ])

    addObject(page.objectContent, [
      `<< /Length ${contentLength} >>\nstream\n${contentStream}\nendstream`
    ])

    addObject(page.objectImage, [
      `<< /Type /XObject /Subtype /Image /Width ${page.pixelWidth} /Height ${page.pixelHeight} ` +
      `/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ${page.imageBytes.length} >>\nstream\n`,
      page.imageBytes,
      '\nendstream'
    ])
  })

  const xrefOffset = currentOffset
  pushPart(`xref\n0 ${objectCount + 1}\n`)
  pushPart('0000000000 65535 f \n')
  for (let i = 1; i <= objectCount; i++) {
    pushPart(`${String(offsets[i]).padStart(10, '0')} 00000 n \n`)
  }
  pushPart(`trailer\n<< /Size ${objectCount + 1} /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF`)

  return new Blob(parts, { type: 'application/pdf' })
}
