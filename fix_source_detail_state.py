import sys
with open('frontend/src/components/SourceDetail.jsx', 'r') as f:
    text = f.read()

new_state = '''
  const [genericData, setGenericData] = useState(null)
  const [genericLoading, setGenericLoading] = useState(false)

  const fetchGenericData = async () => {
    setGenericLoading(true)
    try {
        let endpoint = \/api/\/status\
        if (sourceType === 'aws' || sourceType === 'arg') {
            endpoint = '/api/observations/status'
        }
        const res = await apiFetch(endpoint)
        if (res.ok) {
            setGenericData(await res.json())
        } else {
            setGenericData({ status: 'error', error: await res.text() })
        }
    } catch(e) {
        setGenericData({ status: 'error', error: String(e) })
    }
    setGenericLoading(false)
  }
'''

text = text.replace('const [satelliteStatus, setSatelliteStatus] = useState(null)', new_state + '\n  const [satelliteStatus, setSatelliteStatus] = useState(null)')

text = text.replace('''
    if (sourceType === 'satellite') {
      fetchAllSatelliteData()
    }
  }, [sourceType])''', '''
    if (sourceType === 'satellite') {
      fetchAllSatelliteData()
    } else {
      fetchGenericData()
    }
  }, [sourceType])''')

with open('frontend/src/components/SourceDetail.jsx', 'w') as f:
    f.write(text)
