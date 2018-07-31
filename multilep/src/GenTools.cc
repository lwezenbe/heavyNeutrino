#include <iostream>
#include "heavyNeutrino/multilep/interface/GenTools.h"

const reco::GenParticle* GenTools::getFirstMother(const reco::GenParticle& gen, const std::vector<reco::GenParticle>& genParticles){
    return (gen.numberOfMothers() == 0) ? nullptr : &genParticles[gen.motherRef(0).key()];
}

const reco::GenParticle* GenTools::getMother(const reco::GenParticle& gen, const std::vector<reco::GenParticle>& genParticles){
    const reco::GenParticle* mom = getFirstMother(gen, genParticles);
    if(!mom) return 0;
    else if(mom->pdgId() == gen.pdgId()) return getMother(*mom, genParticles);
    else return mom;
}

void GenTools::setDecayChain(const reco::GenParticle& gen, const std::vector<reco::GenParticle>& genParticles, std::vector<int>& list){
    if((list.empty() or gen.pdgId()!=list.back()) and gen.pdgId() != 2212) list.push_back(gen.pdgId());
    if(gen.numberOfMothers() > 1) setDecayChain(genParticles[gen.motherRef(1).key()], genParticles, list);
    if(gen.numberOfMothers() > 0) setDecayChain(genParticles[gen.motherRef(0).key()], genParticles, list);
}

bool GenTools::parentGluonIsIncoming(std::vector<int>& list){
  bool gluonEncountered = false;
  for(auto d : list){
    if(d==21) gluonEncountered = true;
    if(gluonEncountered and (abs(d)==6 or d==23 or d==24)) return false;
  }
  return true;
}

double GenTools::getMinDeltaR(const reco::GenParticle& p, const std::vector<reco::GenParticle>& genParticles){
    double minDeltaR = 10;
    for(auto& q : genParticles){
        if(q.pt() < 5)                                                           continue;
        if(fabs(p.pt()-q.pt()) < 0.0001)                                         continue; // same particle
        if(q.status() != 1)                                                      continue;
        if(abs(q.pdgId()) == 12 or abs(q.pdgId()) == 14 or abs(q.pdgId()) == 16) continue;
        minDeltaR = std::min(minDeltaR, deltaR(p.eta(), p.phi(), q.eta(), q.phi()));
    }
    return minDeltaR;
}
