package myAgent;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.Set;

import ai.abstraction.Build;
import ai.abstraction.AbstractAction;
import ai.abstraction.AbstractionLayerAI;
import ai.abstraction.Harvest;
import ai.abstraction.pathfinding.AStarPathFinding;
import ai.abstraction.pathfinding.PathFinding;
import ai.core.AI;
import ai.core.ParameterSpecification;
import rts.GameState;
import rts.PhysicalGameState;
import rts.Player;
import rts.PlayerAction;
import rts.ResourceUsage;
import rts.units.Unit;
import rts.units.UnitType;
import rts.units.UnitTypeTable;

public class MyAgent extends AbstractionLayerAI {

  UnitTypeTable m_utt = null;
  Random r = new Random();
  UnitType workerType;
  UnitType baseType;
  UnitType barracksType;
  UnitType rangedType;
  UnitType lightType;
  UnitType heavyType;

  // Crear un diccionario (HashMap) con la correspondencia entre la anchura del mapa y los ciclos de juego
  Map<Integer, Integer> mapCycles = new HashMap<>();
  
  // Status variables
  int nBases = 0;
  int nBarracks = 0;
  int nWorkers = 0;
  int nLight = 0;
  int nRanged = 0;
  int nHeavy = 0;
  int nUnits = 0;
  List<Unit> myBases = new ArrayList<Unit>();
  List<Unit> barracks = new ArrayList<Unit>();
  List<Unit> workers = new ArrayList<Unit>();
  List<Unit> attackWorkers = new ArrayList<Unit>();
  List<Unit> units = new ArrayList<Unit>();
  List<Unit> myResources = new ArrayList<Unit>();
  int resourcesUsed = 0;
  boolean buildingBase = false;
  boolean buildingBarracks = false;

  int nEnemyBases = 0;
  int nEnemyBarracks = 0;
  int nEnemyWorkers = 0;
  int nEnemyLight = 0;
  int nEnemyRanged = 0;
  int nEnemyHeavy = 0;
  int nEnemyUnits = 0;
  List<Unit> enemyBases = new ArrayList<Unit>();
  List<Unit> enemyResources = new ArrayList<Unit>();

  int nMapResources = 0;
  int enemyXDirection = 1;
  int enemyYDirection = -1;
  int diagonal = 0;

  int strategy = 1;

  // Parameters to optimize
  double dEnemyDanger = 0.2;
  double pUnits = 0.82;
  double pTime = 0.85;

  int nHarvestWorkers= 3;
  int nAttackWorkers = 0;
  double probLight = 0.7;
  double probRange = 0.3;
  double probHeavy = 0;
  double dBaseBarracks = 0.12;
  double dUnitBuilding = 0.25;

  // This is the default constructor that microRTS will call:
  public MyAgent(UnitTypeTable utt, double dEnemyDanger, double pUnits,
  double pTime,  int nHarvestWorkers, int nAttackWorkers,  double probLight,
  double probRange,  double probHeavy, double dBaseBarracks, double dUnitBuilding) {
    this(utt, new AStarPathFinding());
    this.dEnemyDanger = dEnemyDanger;
    this.pUnits = pUnits;
    this.pTime = pTime;
    this.nHarvestWorkers = nHarvestWorkers;
    this.nAttackWorkers = nAttackWorkers;
    this.probLight = probLight;
    this.probRange = probRange;
    this.probHeavy = probHeavy;
    this.dBaseBarracks = dBaseBarracks;
    this.dUnitBuilding = dUnitBuilding;
  }

  public MyAgent(UnitTypeTable utt) {
    this(utt, new AStarPathFinding());

  }

  public MyAgent(UnitTypeTable utt, PathFinding a_pf) {
    super(a_pf);
    reset(utt);

    // Agregar las correspondencias según la información proporcionada
    mapCycles.put(8, 4000);   // 8x8 maps
    mapCycles.put(16, 5000);  // 16x16 maps
    mapCycles.put(24, 6000);  // 24x24 maps
    mapCycles.put(32, 7000);  // 32x32 maps
    mapCycles.put(64, 10000); // 64x64 maps
  }

  // This will be called by microRTS when it wants to create new instances of this bot (e.g., to play multiple games).
  public AI clone() {
    return new MyAgent(m_utt, pf);
  }

  
  // This will be called once at the beginning of each new game:    
  public void reset() {
    super.reset();
  }


  public void reset(UnitTypeTable utt) {
    m_utt = utt;
    workerType = m_utt.getUnitType("Worker");
    baseType = m_utt.getUnitType("Base");
    barracksType = m_utt.getUnitType("Barracks");
    rangedType = m_utt.getUnitType("Ranged");
    lightType = m_utt.getUnitType("Light");
    heavyType = m_utt.getUnitType("Heavy");
  }

  public void initializeStatusVars(GameState gs){
    nBases = 0;
    nBarracks = 0;
    nWorkers = 0;
    nLight = 0;
    nRanged = 0;
    nHeavy = 0;
    nUnits = 0;
    myBases = new ArrayList<Unit>();
    barracks = new ArrayList<Unit>();
    workers = new ArrayList<Unit>();
    attackWorkers = new ArrayList<Unit>();
    units = new ArrayList<Unit>();
    myResources = new ArrayList<Unit>();
    buildingBase = false;
    buildingBarracks = false;
    resourcesUsed = 0;

    nEnemyBases = 0;
    nEnemyBarracks = 0;
    nEnemyWorkers = 0;
    nEnemyLight = 0;
    nEnemyRanged = 0;
    nEnemyHeavy = 0;
    nEnemyUnits = 0;
    enemyBases = new ArrayList<Unit>();
    enemyResources = new ArrayList<Unit>();

    nMapResources = 0;
    enemyXDirection = 1;
    enemyYDirection = -1;

    diagonal = gs.getPhysicalGameState().getHeight() + gs.getPhysicalGameState().getWidth();
  }

  // Update the variables employed to take decisions
  public void updateStatusVars(int player, GameState gs) {
    initializeStatusVars(gs);
    PhysicalGameState pgs = gs.getPhysicalGameState();
    Player p = gs.getPlayer(player);

    // units and buildings
    for (Unit u : pgs.getUnits()) {
      if (u.getType() == workerType) {
        if (u.getPlayer() == p.getID()){
          nWorkers++;
          if (nWorkers < nHarvestWorkers){
            workers.add(u);
          } else {
            attackWorkers.add(u);
          }
        } else {
          nEnemyWorkers++;
        }
      } else if (u.getType() == baseType) {
        if (u.getPlayer() == p.getID()){
          nBases++;
          myBases.add(u);
        } else {
          nEnemyBases++;
          enemyBases.add(u);
        }
      } else if (u.getType() == barracksType) {
        if (u.getPlayer() == p.getID()){
          barracks.add(u);
          nBarracks++;
        } else
          nEnemyBarracks++;
      } else if (u.getType() == lightType) {
        if (u.getPlayer() == p.getID()){
          units.add(u);
          nLight++;
          nUnits++;
        } else {
          nEnemyLight++;
          nEnemyUnits++;
        }
      } else if (u.getType() == heavyType) {
        if (u.getPlayer() == p.getID()){
          units.add(u);
          nHeavy++;
          nUnits++;
        } else {
          nEnemyHeavy++;
          nEnemyUnits++;
        }
      } else if (u.getType() == rangedType) {
        if (u.getPlayer() == p.getID()){
          units.add(u);
          nRanged++;
          nUnits++;          
        } else {
          nEnemyRanged++;
          nEnemyUnits++;
        }          
      }
    }

    // resources
    if (myBases.size() > 0 && enemyBases.size() > 0){
      for (Unit u : pgs.getUnits()) {
        if (u.getType().isResource) {
          nMapResources++;
          if (distanceBetween(u, myBases.get(0)) <= distanceBetween(u, enemyBases.get(0))){
            myResources.add(u);
          } else {
            enemyResources.add(u);
          }
        }
      }

      enemyXDirection = Integer.signum(enemyBases.get(0).getX() - myBases.get(0).getX());
      enemyYDirection = Integer.signum(enemyBases.get(0).getY() - myBases.get(0).getY());
    } else {
      for (Unit u : pgs.getUnits()) {
        if (u.getType().isResource) {
          nMapResources++;
          myResources.add(u);
        }
      }
    }
  }

  private int distanceBetween(Unit u1, Unit u2){
    return Math.abs(u1.getX() - u2.getX()) + Math.abs(u1.getY() - u2.getY());
  }

  private int selectStrategy(Player p, GameState gs){
    int strategy = 1;
    int width = gs.getPhysicalGameState().getWidth();

    // Determine the game cycles for the map
    double cycles;
    if (mapCycles.containsKey(width)) {
        cycles = (double) mapCycles.get(width);
    } else {
        cycles = 14000;
    }

    if ((nUnits*pUnits >= nEnemyUnits && nUnits > 0) || nUnits == 0) {
      strategy = 2;
    }
    
    if (nBases == 0 || (gs.getTime() > ((int) (pTime*cycles)))){
      strategy = 3;
    }

    for (Unit b: myBases) {
      if (enemiesNearBase(b, p, gs.getPhysicalGameState())){
        strategy = 0;
        return strategy;
      }
    }

    return strategy;
  }
  
  @Override
  public PlayerAction getAction(int player, GameState gs) throws Exception {
    PhysicalGameState pgs = gs.getPhysicalGameState();
    Player p = gs.getPlayer(player);

    updateStatusVars(player, gs);
    strategy = selectStrategy(p, gs);
    // if (gs.getTime()%100 == 0)
    // System.out.println(strategy);

    // behavior of workers:
    workersBehavior(workers, p, gs);
    for (Unit u: attackWorkers){
      meleeUnitBehavior(u, p, gs);
    }

    // behavior of barracks:
    for (Unit b : barracks) {
      if (b.isIdle(gs)) {
        barracksBehavior(b, p, pgs);
      }
    }

    // behavior of bases:
    for (Unit base: myBases)
      baseBehavior(base, p, gs);

    // behavior of melee units:
    for (Unit u : units) {
      // if (gs.getActionAssignment(u) == null) {
      meleeUnitBehavior(u, p, gs);
    }

    return translateActions(player, gs);
  }


  @Override
  public List<ParameterSpecification> getParameters() {
    List<ParameterSpecification> parameters = new ArrayList<>();

    parameters.add(new ParameterSpecification("PathFinding", PathFinding.class, new AStarPathFinding()));

    return parameters;
  }

  public void baseBehavior(Unit u, Player p, GameState gs) {
    int qtdWorkLim = nHarvestWorkers + nAttackWorkers;
    if (nBases > 0){
      qtdWorkLim = nHarvestWorkers + nAttackWorkers;
    }

    if ((nWorkers < qtdWorkLim)
      && (p.getResources() - resourcesUsed) >= workerType.cost && u.isIdle(gs)) {
      train(u, workerType);
      resourcesUsed += workerType.cost;
    }
  }

  /* Trains Ranged or Heavy Units */
  public void barracksBehavior(Unit u, Player p, PhysicalGameState pgs) {
    double number = r.nextDouble();

    if (number < probLight){
      trainUnitType(lightType, u, p);
    } else if (number < probLight + probHeavy){
      trainUnitType(heavyType, u, p);
    } else if (number < probLight + probHeavy + probRange){
      trainUnitType(rangedType, u, p);
    }
  }


  public void trainUnitType(UnitType t, Unit barracks, Player p){
    if (p.getResources() - resourcesUsed >= (t.cost)) {
      train(barracks, t);
      resourcesUsed += t.cost;
    }
  }

  
  public void meleeUnitBehavior(Unit u, Player p, GameState gs){
    PhysicalGameState pgs = gs.getPhysicalGameState();
    Unit closestEnemy = null;
    int closestDistance = gs.getPhysicalGameState().getHeight();

    for (Unit u2 : pgs.getUnits()) {
      if (u2.getPlayer() >= 0 && u2.getPlayer() != p.getID()) {
        int d = Math.abs(u2.getX() - u.getX()) + Math.abs(u2.getY() - u.getY());
        if ((d < closestDistance || closestEnemy == null)){
          if (gs.getPhysicalGameState().getHeight() > 16 ||
            (pf.pathToPositionInRangeExists(u2, u.getX()*pgs.getWidth() + u.getY(), u.getAttackRange(), gs, null) || d == 1) ) {
            closestEnemy = u2;
            closestDistance = d;
          }
        }          
      }
    }

    if (strategy == 0 || strategy == 3 || strategy == 2){
      if (closestEnemy != null) {
        this.attack(u, closestEnemy);
      } else {
        moveRandomly(u, pgs);
      }
    } else {
      if (closestEnemy != null && closestDistance < dEnemyDanger*diagonal) {
        this.attack(u, closestEnemy);
      } else if ((nearBuilding(u, p, pgs) || nearMyResources(u, p, pgs)) 
                  && gs.getActionAssignment(u) == null) {
        int distanceX = r.nextInt((int)(diagonal*dUnitBuilding)) * enemyXDirection, 
            distanceY = r.nextInt((int)(diagonal*dUnitBuilding)) * enemyYDirection;
        int xPos = u.getX() + distanceX;
        int yPos = u.getY() + distanceY;

        if (pf.pathToPositionInRangeExists(u, xPos*pgs.getWidth()+yPos, 1, gs, null)){
          move(u, xPos, yPos);
        } else {
          moveRandomly(u, pgs);
        }
      } else {
        moveRandomly(u, pgs);
      }
    }
  }

  public boolean moveRandomly(Unit u, PhysicalGameState pgs){
    int xPos = r.nextInt(3) + u.getX() - 1;
    int yPos = r.nextInt(3) + u.getY() - 1;
    xPos = xPos <= 0 ? 1 : xPos >= pgs.getWidth() ? pgs.getWidth() - 1 : xPos;
    yPos = yPos <= 0 ? 1 : yPos >= pgs.getHeight() ? pgs.getHeight() - 1 : yPos;
    move(u, xPos, yPos); 
    return true;
  }

  public boolean nearBuilding(Unit u, Player p, PhysicalGameState pgs){
    boolean nearBuilding = false;
    
    for (Unit u2 : pgs.getUnits()) {
      if (u2.getPlayer() >= 0 && u2.getPlayer() == p.getID()) {
        if (u2.getType() == barracksType || u2.getType() == baseType) {
          int d = Math.abs(u2.getX() - u.getX()) + Math.abs(u2.getY() - u.getY());
          if (d < dUnitBuilding*diagonal){
            nearBuilding = true;
          }
        }
      }
    }

    return nearBuilding;
  }

  public boolean nearMyResources(Unit u, Player p, PhysicalGameState pgs){
    boolean nearResources = false;
    
    for (Unit res : myResources) {
      int d = Math.abs(res.getX() - u.getX()) + Math.abs(res.getY() - u.getY());
      if (d < 4){
        nearResources = true;
      }
    }

    return nearResources;
  }

  public boolean enemiesNearBase(Unit u, Player p, PhysicalGameState pgs){
    int diagonal = pgs.getHeight() + pgs.getWidth();
    
    for (Unit u2 : pgs.getUnits()) {
      if (u2.getPlayer() >= 0 && u2.getPlayer() != p.getID()) {
        if (u2.getType() == lightType || u2.getType() == workerType 
          || u2.getType() == rangedType || u2.getType() == heavyType) {
          int d = distanceBetween(u, u2);
          if (d < diagonal*dEnemyDanger){
            return true;
          }
        }
      }
    }

    return false;
  }

  public void workersBehavior(List<Unit> workers, Player p, GameState gs){
    PhysicalGameState pgs = gs.getPhysicalGameState();
    List<Unit> constructionWorkers = new ArrayList<>();
    List<Unit> harvestWorkers = new ArrayList<>();
    int i = 0;

    if (workers.isEmpty()) {
      return;
    } else {
      harvestWorkers.add(workers.remove(0));

      for (Unit w : workers){
        if (this.actions.get(w) instanceof Build){
          constructionWorkers.add(w);
        } else {
          harvestWorkers.add(w);
        }
      }
    }

    // if don't have base, build one
    List<Integer> reservedPositions = new ArrayList<>();
    if (nBases == 0 && !harvestWorkers.isEmpty() && constructionWorkers.isEmpty()) {
      if (p.getResources() >= baseType.cost + resourcesUsed) {
        Unit u = harvestWorkers.remove(0);
        buildIfNotAlreadyBuilding(u, baseType, u.getX(), u.getY(), reservedPositions, p, pgs);
        resourcesUsed += baseType.cost;
      }
    }

    // if dont have enough barracks (same as bases), build barracks
    if ((probLight + probHeavy + probRange) > 0 && nBarracks < nBases && !harvestWorkers.isEmpty() && constructionWorkers.isEmpty()) {
      if (p.getResources() >= barracksType.cost + resourcesUsed) {
        Unit worker = null;
        int closestDistance = 0;
        int idxWorker = 0;
        int mapHeight = pgs.getHeight();
        int mapWidth = pgs.getWidth();
        int xPos = 0, yPos = 0;
        
        if (myBases.size() > 0){
          Unit base = myBases.get(myBases.size()-1);
          xPos = base.getX() + ((int) Math.ceil(dBaseBarracks * (double)mapWidth)) * enemyXDirection;
          yPos = base.getY() + ((int) Math.ceil(dBaseBarracks * (double)mapHeight)) * enemyYDirection;
          xPos = xPos < 1 ? 1 : (xPos > mapWidth) ? mapWidth-1 : xPos;
          yPos = yPos < 1 ? 1 : (yPos > mapHeight) ? mapHeight-1 : yPos;

          int tries = 0;
          while (gs.getPhysicalGameState().getTerrain(xPos, yPos) != 0 && tries < 3){
            xPos = xPos - enemyXDirection;
            yPos = yPos - enemyYDirection;
            xPos = xPos < 1 ? 1 : (xPos > mapWidth) ? mapWidth-1 : xPos;
            yPos = yPos < 1 ? 1 : (yPos > mapHeight) ? mapHeight-1 : yPos;
            tries++;
          }


          for (i = 0; i < harvestWorkers.size(); i++) {
            int d = Math.abs(base.getX() - harvestWorkers.get(i).getX()) + Math.abs(base.getY() - harvestWorkers.get(i).getY());
            if (d < closestDistance || worker == null) {
              worker = harvestWorkers.get(i);
              closestDistance = d;
              idxWorker = i;
            }
          }

          worker = harvestWorkers.remove(idxWorker);
        } else {
          worker = harvestWorkers.remove(0);
          xPos = worker.getX();
          yPos = worker.getY();
        }

        buildIfNotAlreadyBuilding(worker, barracksType, xPos, yPos, reservedPositions, p, pgs);
        resourcesUsed += barracksType.cost;
      }
    }

    // Build a new base near resources (if there are enough)
    if (nBarracks != 0 && !harvestWorkers.isEmpty()) {
      List<Unit> otherResources = new ArrayList<>(otherResourcePoint(p, pgs));
      if (otherResources.size() > 2) {
        if (p.getResources() >= baseType.cost + resourcesUsed) {
          Unit u = harvestWorkers.remove(0);
          buildIfNotAlreadyBuilding(u, baseType, otherResources.get(0).getX()+1, otherResources.get(0).getY()-1, reservedPositions, p, pgs);
          resourcesUsed += baseType.cost;
        }
      }
    }

    if (!harvestWorkers.isEmpty()){
      if (myResources.size() > 0){
        // harvest with all the harvest workers
        harvestWorkers(harvestWorkers, p, gs);
      } else {
        for (Unit worker : harvestWorkers)
          meleeUnitBehavior(worker, p, gs);
      }
    }
  }

  protected List<Unit> otherResourcePoint(Player p, PhysicalGameState pgs){
    Set<Unit> nearResources = new HashSet<>();
    Set<Unit> otherResources = new HashSet<>();

    for (Unit base : myBases) {
      List<Unit> closestUnits = new ArrayList<>(pgs.getUnitsAround(base.getX(), base.getY(), 10));
      for (Unit closestUnit : closestUnits) {
        if (closestUnit.getType().isResource) {
          nearResources.add(closestUnit);
        }
      }
    }

    for (Unit res : myResources) {
      if (!nearResources.contains(res)) {
        otherResources.add(res);
      }
    }

    return new ArrayList<>(otherResources);
  }

  protected void harvestWorkers(List<Unit> freeWorkers, Player p, GameState gs) {
    PhysicalGameState pgs = gs.getPhysicalGameState();

    for (Unit u : freeWorkers) {
      Unit closestBase = null;
      Unit closestResource = null;
      int closestDistance = 0;
      for (Unit res : myResources) {
        int d = Math.abs(res.getX() - u.getX()) + Math.abs(res.getY() - u.getY());
        if ((closestResource == null || d < closestDistance) 
        && (pf.pathToPositionInRangeExists(u, res.getX()*pgs.getWidth() + res.getY(), 1, gs, null) || d == 1)) {
          closestResource = res;
          closestDistance = d;
        }
      }
      closestDistance = 0;

      for (Unit base : myBases) {
        int d = Math.abs(base.getX() - u.getX()) + Math.abs(base.getY() - u.getY());
        if (closestBase == null || d < closestDistance) {
          closestBase = base;
          closestDistance = d;
        }
      }

      if (closestResource != null && closestBase != null) {
        AbstractAction aa = getAbstractAction(u);
        if (aa instanceof Harvest) {
          Harvest h_aa = (Harvest) aa;
          if (h_aa.getTarget() != closestResource || h_aa.getBase() != closestBase) {
            harvest(u, closestResource, closestBase);
          }
        } else {
          harvest(u, closestResource, closestBase);
        }
      }
    }
  }

// MYAGENT END
}