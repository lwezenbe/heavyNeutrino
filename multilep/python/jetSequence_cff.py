import FWCore.ParameterSet.Config as cms
import os

def addJetSequence(process, isData):

  #
  # Latest JEC through globaltag, see https://twiki.cern.ch/twiki/bin/viewauth/CMS/JECDataMC
  # Has (at time of writing) no effect (Moriond2017 miniAOD contains latest JEC)
  #
  process.load('JetMETCorrections.Configuration.JetCorrectors_cff')
  process.load('Configuration.StandardSequences.MagneticField_cff')  # needed for pfImpactParameterTagInfos
  if isData: jetCorrectorLevels = ['L1FastJet', 'L2Relative', 'L3Absolute','L2L3Residual']
  else:      jetCorrectorLevels = ['L1FastJet', 'L2Relative', 'L3Absolute']

  from PhysicsTools.PatAlgos.tools.jetTools import updateJetCollection
  updateJetCollection(
     process,
     jetSource = cms.InputTag('slimmedJets'),
     labelName = 'UpdatedJEC',
     jetCorrections = ('AK4PFchs', cms.vstring(jetCorrectorLevels), 'None'),
     # DeepCSV twiki: https://twiki.cern.ch/twiki/bin/view/CMS/DeepFlavour
     btagDiscriminators = [
       'pfCombinedSecondaryVertexV2BJetTags',
       'pfDeepCSVJetTags:probudsg',
       'pfDeepCSVJetTags:probb',
       'pfDeepCSVJetTags:probc',
       'pfDeepCSVJetTags:probbb',
      #'pfDeepCSVJetTags:probcc', # not available in CMSSW_9_X_Y, also not really needed for us
     ]
  )

  if os.environ['CMSSW_BASE'].count('CMSSW_9'):                                                                     # From CMSSW_9_X, the patAlgosToolsTask contains the whole updateJetCollection sequence
    process.jetSequence = cms.Sequence(process.patAlgosToolsTask)
  else:
    process.jetSequence = cms.Sequence(process.patJetCorrFactorsUpdatedJEC * process.updatedPatJetsUpdatedJEC *
                                       process.pfImpactParameterTagInfosUpdatedJEC *
                                       process.pfSecondaryVertexTagInfosUpdatedJEC *
                                       process.pfCombinedSecondaryVertexV2BJetTagsUpdatedJEC *
                                       process.patJetCorrFactorsTransientCorrectedUpdatedJEC *
                                       process.pfInclusiveSecondaryVertexFinderTagInfosUpdatedJEC *
                                       process.pfDeepCSVTagInfosUpdatedJEC *
                                       process.pfDeepCSVJetTagsUpdatedJEC *
                                       process.updatedPatJetsTransientCorrectedUpdatedJEC *
                                       process.selectedUpdatedPatJetsUpdatedJEC)

  #
  # Jet energy resolution, see https://twiki.cern.ch/twiki/bin/view/CMS/JetResolution#Smearing_procedures
  # Run three times the SmearedPATJetProducer for nominal, up and down variations
  #
  if not isData:
    # Set up access to JER database as it is not included in the global tag
    # yet. The snippet is adapted from [1].  The main change is using the
    # FileInPath extention to access the database file [2].
    # [1] https://github.com/cms-met/cmssw/blob/8b17ab5d8b28236e2d2215449f074cceccc4f132/PhysicsTools/PatAlgos/test/corMETFromMiniAOD.py
    # [2] https://hypernews.cern.ch/HyperNews/CMS/get/db-aligncal/58.html
    from CondCore.DBCommon.CondDBSetup_cfi import CondDBSetup
    process.jerDB = cms.ESSource(
        'PoolDBESSource', CondDBSetup,
        connect = cms.string('sqlite_fip:heavyNeutrino/multilep/data/JER/Summer16_25nsV1_80X_' + ('DATA' if isData else 'MC') + '.db'),
        toGet = cms.VPSet(
            cms.PSet(
                record = cms.string('JetResolutionRcd'),
                tag = cms.string('JR_Summer16_25nsV1_80X_' + ('DATA' if isData else 'MC') + '_PtResolution_AK4PFchs'),
                label = cms.untracked.string('AK4PFchs_pt')
            ),
            cms.PSet(
                record = cms.string('JetResolutionRcd'),
                tag = cms.string('JR_Summer16_25nsV1_80X_' + ('DATA' if isData else 'MC') + '_PhiResolution_AK4PFchs'),
                label = cms.untracked.string('AK4PFchs_phi')
            ),
            cms.PSet(
                record = cms.string('JetResolutionScaleFactorRcd'),
                tag = cms.string('JR_Summer16_25nsV1_80X_' + ('DATA' if isData else 'MC') + '_SF_AK4PFchs'),
                label = cms.untracked.string('AK4PFchs')
            ),
        )
    )
    process.jerDBPreference = cms.ESPrefer('PoolDBESSource', 'jerDB')


    for (i, j) in [(0, ''), (-1, 'Down'), (1, 'Up')]:
      jetSmearing = cms.EDProducer('SmearedPATJetProducer',
            src          = cms.InputTag('selectedUpdatedPatJetsUpdatedJEC'),
            enabled      = cms.bool(True),
            rho          = cms.InputTag("fixedGridRhoFastjetAll"),
            algo         = cms.string('AK4PFchs'),
            algopt       = cms.string('AK4PFchs_pt'),
            genJets      = cms.InputTag('slimmedGenJets'),
            dRMax        = cms.double(0.2),
            dPtMaxFactor = cms.double(3),
            debug        = cms.untracked.bool(False),
            variation    = cms.int32(i),
      )
      setattr(process, 'slimmedJetsCorrectedAndSmeared'+j, jetSmearing)
      process.jetSequence *= jetSmearing

  # Propagate JEC to MET (need to add fullPatMetSequence to path) (maybe good to add here link to a twiki page, if it exist)
  # from PhysicsTools.PatUtils.tools.runMETCorrectionsAndUncertainties import runMetCorAndUncFromMiniAOD   # currently broken
  from heavyNeutrino.multilep.runMETCorrectionsAndUncertainties import runMetCorAndUncFromMiniAOD
  runMetCorAndUncFromMiniAOD(process, isData=isData)
